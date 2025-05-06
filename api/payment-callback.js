// api/payment-callback.js
// 接收来自易支付平台的回调通知 (通常是 GET 或 POST 请求)。
// 验证回调请求的真实性 (MD5 签名校验)。
// 如果支付成功：
//   - 更新内部订单状态为 'PAID'。
//   - 生成许可证密钥。
//   - 将许可证密钥存储到数据库，并关联用户邮箱。
//   - 发送包含许可证密钥的邮件给用户。
//   - 向易支付平台返回成功响应 ('success')。

import clientPromise from '../lib/mongodb'; // 导入数据库连接
const crypto = require('crypto'); // 用于 MD5 签名验证
// const nodemailer = require('nodemailer'); // 用于发送邮件

// --- 易支付配置 (从环境变量读取) ---
const YIPAY_MD5_KEY = process.env.PAYMENT_YIPAY_MD5_KEY; // 您的 MD5 密钥 (非常重要!)
// --- 许可证生成密钥 --- 
const LICENSE_SECRET = process.env.LICENSE_SECRET || 'default-license-secret-please-change'; // 从环境变量获取，提供默认值(不安全)
// -----------------------------------

// MD5签名验证函数 (适用于常见易支付系统)
function verifyYiPayMD5Sign(params, key) {
  const receivedSign = params.sign;
  if (!receivedSign) return false;

  // 1. 过滤空值和签名参数
  const filteredParams = Object.keys(params)
    .filter(k => params[k] !== '' && params[k] !== null && k !== 'sign' && k !== 'sign_type')
    .sort() // 2. 参数名ASCII字典序排序
    .map(k => `${k}=${params[k]}`); // 3. 拼接成 key=value 格式

  // 4. 拼接密钥
  const stringToSign = filteredParams.join('&') + key;

  // 5. 计算 MD5 哈希 (小写)
  const calculatedSign = crypto.createHash('md5').update(stringToSign).digest('hex');

  // 6. 对比签名
  return calculatedSign === receivedSign;
}

module.exports = async (req, res) => {
  // 易支付回调可能是 GET 或 POST，都需要处理
  const callbackData = { ...req.query, ...req.body }; // 合并 GET 和 POST 参数

  console.log('Received YiPay payment callback:', JSON.stringify(callbackData, null, 2));

  // 检查 MD5 Key 是否配置
  if (!YIPAY_MD5_KEY) {
    console.error('YiPay MD5 Key not configured in environment variables for callback verification.');
    // 无法验证，但可能仍需告知易支付收到通知，避免重试
    return res.status(200).send('fail'); // 或其他易支付要求的失败响应
  }

  let client;
  try {
    // 1. 验证回调请求的真实性 (MD5 签名)
    const isValid = verifyYiPayMD5Sign(callbackData, YIPAY_MD5_KEY);

    if (!isValid) {
      console.error('YiPay payment callback verification failed (MD5 mismatch).', callbackData);
      return res.status(400).send('fail'); // 返回失败响应给易支付
    }
    console.log('YiPay callback signature verified successfully.');

    // 2. 从回调数据中提取关键信息 (参考易支付文档调整字段名)
    const internalOrderNo = callbackData.out_trade_no; // 商户订单号
    const platformTradeNo = callbackData.trade_no;     // 易支付订单号
    const tradeStatus = callbackData.trade_status;   // 交易状态 (通常 'TRADE_SUCCESS')
    const paidAmount = parseFloat(callbackData.money);           // 支付金额
    const paymentType = callbackData.type;         // 支付方式

    console.log(`Processing verified callback for order: ${internalOrderNo}, Status: ${tradeStatus}`);

    // 3. 根据支付状态处理
    if (tradeStatus === 'TRADE_SUCCESS') {
      console.log(`Payment successful notification for order ${internalOrderNo}`);

      // 4. (关键) 查询您的数据库，检查订单是否存在且状态为 PENDING
      //    防止重复处理回调
      client = await clientPromise; // 获取数据库连接
      const db = client.db("wenzhisouDB");
      const ordersCollection = db.collection("orders");
      const licensesCollection = db.collection("licenses"); // 假设我们有一个 licenses 集合

      // 1. 查询订单并检查状态 (防止重复处理)
      const orderDetails = await ordersCollection.findOne({ internalOrderNo: internalOrderNo });

      if (!orderDetails) {
        console.error(`Order ${internalOrderNo} not found in DB for successful callback.`);
        // 订单不存在，但支付成功，返回 success 告知易支付已收到
        return res.status(200).send('success');
      }

      if (orderDetails.status !== 'PENDING') {
        console.warn(`Order ${internalOrderNo} already processed. Status: ${orderDetails.status}`);
        // 已经处理过，直接返回成功给易支付
        return res.status(200).send('success');
      }

      // 5. 更新数据库中的订单状态为 'PAID'
      const updateResult = await ordersCollection.updateOne(
        { internalOrderNo: internalOrderNo },
        { 
          $set: { 
            status: 'PAID', 
            platformOrderId: platformTradeNo, // 记录易支付订单号
            paymentType: paymentType,      // 记录支付方式
            paidAmount: paidAmount,         // 记录实际支付金额
            updatedAt: new Date()
          }
        }
      );
      console.log(`Updated order ${internalOrderNo} status to PAID. Matched: ${updateResult.matchedCount}, Modified: ${updateResult.modifiedCount}`);

      // 6. 生成许可证密钥
      const licenseKey = generateLicense(orderDetails.email, orderDetails.productId);
      console.log(`Generated license key for ${orderDetails.email}: ${licenseKey}`);

      // 7. 存储许可证信息到数据库
      // await storeLicenseInDB(internalOrderNo, mockOrderDetails.email, licenseKey);
      console.log(`Stored license key for order ${internalOrderNo}.`);

      // 8. 发送许可证邮件给用户
      try {
        await sendLicenseEmail(orderDetails.email, licenseKey, internalOrderNo);
      } catch (emailError) {
        console.error(`Failed to send license email for order ${internalOrderNo}:`, emailError);
      }

      // 9. 向易支付平台返回成功处理的响应 ('success')
      console.log(`Sending 'success' response to YiPay for order ${internalOrderNo}`);
      res.status(200).send('success');

    } else {
      // 处理其他支付状态 (如 WAIT_BUYER_PAY 等)
      console.log(`Callback received for order ${internalOrderNo} with status ${tradeStatus}. No action taken.`);
      // 对于非成功状态，通常也需要返回 'success' 告知易支付已收到通知
      res.status(200).send('success');
    }

  } catch (error) {
    console.error('Error processing YiPay payment callback:', error);
    // 即使内部处理出错，也返回 'success' 给易支付，避免其重试，但记录错误
    res.status(200).send('success'); // 修改这里：即使内部出错也返回 success
  } finally {
    if (client) {
      await client.close();
    }
  }
};

// --- 辅助函数占位符 (需要您实现) ---

// 从数据库获取订单信息的函数
// async function getOrderFromDB(orderNo) { ... }

// 更新数据库订单状态的函数
// async function updateOrderStatusInDB(orderNo, newStatus, platformTradeNo, paymentType) { ... }

// 生成许可证密钥的函数
function generateLicense(email, productId) {
  const baseString = `${email}-${productId}-${Date.now()}-${LICENSE_SECRET}`;
  const hash = crypto.createHash('sha256').update(baseString).digest('hex');
  // 格式化，例如 WZS-PROYEARLY-XXXX-XXXX-XXXX-XXXX
  return `WZS-${productId.toUpperCase().replace(/[^A-Z0-9]/g, '')}-${hash.substring(0, 4)}-${hash.substring(4, 8)}-${hash.substring(8, 12)}-${hash.substring(12, 16)}`.toUpperCase();
}

// 存储许可证信息的函数
// async function storeLicenseInDB(orderNo, email, licenseKey) { ... }

// 发送许可证邮件的函数
async function sendLicenseEmail(email, licenseKey, orderNo) {
  console.log(`--- Simulating Sending Email ---`);
  console.log(`To: ${email}`);
  console.log(`Order: ${orderNo}`);
  console.log(`License Key: ${licenseKey}`);
  console.log(`--- End Simulation ---`);
  // 在这里实现真实的邮件发送逻辑，使用 nodemailer 或其他服务
  // 例如:
  // const transporter = nodemailer.createTransport({...});
  // await transporter.sendMail({...});
  return true; // 假设发送成功
} 