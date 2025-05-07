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
const nodemailer = require('nodemailer'); // 确保 nodemailer 已导入
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
      const licenseDocument = {
        orderNo: internalOrderNo,
        email: orderDetails.email,
        productId: orderDetails.productId,
        licenseKey: licenseKey,
        createdAt: new Date(),
      };
      await licensesCollection.insertOne(licenseDocument);
      console.log(`Stored license key for order ${internalOrderNo} to licenses collection.`);

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
  console.log(`Attempting to send license email to: ${email} for order: ${orderNo}`);

  // 1. 创建 Transporter 对象 (配置您的邮件服务)
  //    重要：请使用环境变量存储敏感信息！
  const transporter = nodemailer.createTransport({
    host: process.env.EMAIL_SMTP_HOST, // 例如：'smtp.example.com'
    port: parseInt(process.env.EMAIL_SMTP_PORT, 10) || 587, // 例如：587 或 465
    secure: (process.env.EMAIL_SMTP_SECURE === 'true'), // true for 465, false for other ports
    auth: {
      user: process.env.EMAIL_SMTP_USER, // 您的邮箱用户名
      pass: process.env.EMAIL_SMTP_PASS, // 您的邮箱密码或应用专用密码
    },
    tls: {
      // 如果您的SMTP服务器使用自签名证书，可能需要这个
      // rejectUnauthorized: false
    }
  });

  // 2. 定义邮件内容
  const mailOptions = {
    from: `"文智搜支持" <${process.env.EMAIL_FROM_ADDRESS || process.env.EMAIL_SMTP_USER}>`, // 发件人地址
    to: email, // 收件人地址 (从订单详情中获取)
    subject: `您的 文智搜 专业版许可证密钥 - 订单 ${orderNo}`, // 邮件主题
    text: `感谢您购买文智搜专业版！\n\n您的订单号是: ${orderNo}\n您的许可证密钥是: ${licenseKey}\n\n请妥善保管您的密钥。\n\n感谢您的支持！\n文智搜团队`, // 纯文本内容
    html: `
      <p>尊敬的用户，</p>
      <p>感谢您购买文智搜专业版！</p>
      <p>您的订单号是: <strong>${orderNo}</strong></p>
      <p>您的许可证密钥是: <strong>${licenseKey}</strong></p>
      <p>请妥善保管您的密钥。</p>
      <p>如有任何疑问，请随时与我们联系。</p>
      <p>感谢您的支持！<br>文智搜团队</p>
    ` // HTML 内容 (更美观)
  };

  try {
    // 3. 发送邮件
    let info = await transporter.sendMail(mailOptions);
    console.log('License email sent successfully: %s', info.messageId);
    // console.log('Preview URL: %s', nodemailer.getTestMessageUrl(info)); // 仅在用 ethereal.email 测试时有用
    return true;
  } catch (error) {
    console.error(`Error sending license email to ${email} for order ${orderNo}:`, error);
    // 即使邮件发送失败，也不应该影响给易支付返回 'success'
    // 但需要记录错误，以便后续处理 (例如手动补发)
    return false;
  }
} 