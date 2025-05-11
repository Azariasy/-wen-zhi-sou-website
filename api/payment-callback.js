// api/payment-callback.js
// 接收来自易支付平台的回调通知 (通常是 GET 或 POST 请求)。
// 验证回调请求的真实性 (MD5 签名校验)。
// 如果支付成功：
//   - 更新内部订单状态为 'PAID'。
//   - 生成许可证密钥。
//   - 将许可证密钥存储到数据库，并关联用户邮箱。
//   - 发送包含许可证密钥的邮件给用户。
//   - 向易支付平台返回成功响应 ('success')。

// const clientPromise = require('../lib/mongodb'); // 使用 CommonJS 引入 MongoDB 客户端实例
// 实际使用时，您需要确保 ../lib/mongodb.js 文件使用 module.exports 导出了一个 MongoDB clientPromise
// 例如，在 ../lib/mongodb.js 中可能是这样的:
// const { MongoClient } = require('mongodb');
// const uri = process.env.MONGODB_URI;
// const options = {};
// let client;
// let clientPromise;
// if (!process.env.MONGODB_URI) {
//   throw new Error('Please add your Mongo URI to .env.local');
// }
// client = new MongoClient(uri, options);
// clientPromise = client.connect();
// module.exports = clientPromise;
// 如果您直接使用mongodb驱动，而不是通过lib包装，则如下引入：
const { MongoClient } = require('mongodb'); 

const crypto = require('crypto'); // 用于 MD5 签名验证
const nodemailer = require('nodemailer'); // 用于发送邮件

// --- 易支付配置 (从环境变量读取) ---
const YIPAY_MD5_KEY = process.env.PAYMENT_YIPAY_MD5_KEY; // 您的 MD5 密钥 (非常重要!)
// --- 许可证生成密钥 --- 
const LICENSE_SECRET = process.env.LICENSE_SECRET || 'default-license-secret-please-change'; // 从环境变量获取，提供默认值(不安全)
const MONGODB_URI = process.env.MONGODB_URI;
const DB_NAME = process.env.DB_NAME || 'wenzisou'; // 从环境变量读取数据库名，默认为'wenzisou'
// -----------------------------------

// MD5签名验证函数 (适用于常见易支付系统)
function verifyYiPayMD5Sign(params, key) {
  const receivedSign = params.sign;
  if (!receivedSign) {
    log('[SIGN_VALIDATION_ERROR] Callback missing sign parameter.');
    return false;
  }
  if (!key) {
    log('[SIGN_VALIDATION_ERROR] MD5 Key (YIPAY_MD5_KEY) is not configured on the server.');
    return false; // 如果密钥未配置，则无法验证
  }

  const filteredParams = Object.keys(params)
    .filter(k => params[k] !== '' && params[k] !== null && k !== 'sign' && k !== 'sign_type')
    .sort()
    .map(k => `${k}=${params[k]}`); 

  const stringToSign = filteredParams.join('&') + key;
  const calculatedSign = crypto.createHash('md5').update(stringToSign).digest('hex');
  log(`[SIGN_VALIDATION] String to sign: "${stringToSign}"`);
  log(`[SIGN_VALIDATION] Calculated sign: "${calculatedSign}", Received sign: "${receivedSign}"`);
  return calculatedSign === receivedSign;
}

// 辅助函数，用于打印日志时添加时间戳
function log(message) {
    console.log(`[${new Date().toISOString()}] [payment-callback] ${message}`);
}

module.exports = async (req, res) => {
    log('--- Payment callback received ---');
    log(`Request method: ${req.method}`);

    if (req.method !== 'GET') {
        log(`Invalid request method: ${req.method}. Responding with 405.`);
        res.setHeader('Allow', ['GET']);
        return res.status(405).end(`Method ${req.method} Not Allowed`);
    }

    log('Received query parameters:');
    const callbackParams = { ...req.query }; // 复制一份参数，避免直接修改原始req.query
    console.log(callbackParams);

    const {
        pid,
        trade_no,
        out_trade_no,
        type,
        name,
        money,
        trade_status,
        sign,
        sign_type
    } = callbackParams; // 从副本中解构

    log(`Callback Parameters: pid=${pid}, trade_no=${trade_no}, out_trade_no=${out_trade_no}, type=${type}, name=${name}, money=${money}, trade_status=${trade_status}, sign_type=${sign_type}`);

    // --- 1. 验证签名 ---
    if (!YIPAY_MD5_KEY) {
        log('[FATAL_ERROR] YIPAY_MD5_KEY is not set in environment variables. Cannot verify signature.');
        // 即使无法验证签名，通常也建议返回成功给支付平台，避免其不断重试，但要记录严重错误
        return res.status(200).send('success'); // 或者根据易支付文档返回特定错误码，但不建议让其重试
    }

    const isSignValid = verifyYiPayMD5Sign(callbackParams, YIPAY_MD5_KEY);
    if (!isSignValid) {
        log('[SIGNATURE_VERIFICATION_FAILED] Invalid signature. Aborting processing.');
        // 对于签名验证失败，可以考虑不返回 'success'，让支付平台知道有问题，
        // 但具体行为需参考易支付文档关于签名失败时的推荐响应。
        // 有些平台可能要求返回特定错误字符串，或者如果你不返回 success，它会重试。
        // 为安全起见，如果签名不匹配，通常不应继续处理业务逻辑。
        // 但为了防止支付平台因未收到'success'而持续轰炸，这里暂时仍返回success，但已记录严重错误。
        // 在生产环境中，签名失败是严重问题，需要报警和调查。
        return res.status(200).send('success'); // 或根据文档返回 'fail' 等，但要注意是否会引起重试
    }
    log('[SIGNATURE_VERIFICATION_SUCCESS] Signature is valid.');

    // --- 2. 检查交易状态 trade_status ---
    if (trade_status !== 'TRADE_SUCCESS') {
        log(`[TRADE_STATUS_NOT_SUCCESS] Trade status is "${trade_status}", not "TRADE_SUCCESS". Order: ${out_trade_no}. No action taken, but responding success to Yipay.`);
        return res.status(200).send('success');
    }
    log(`[TRADE_STATUS_SUCCESS] Trade status is "TRADE_SUCCESS" for order ${out_trade_no}.`);

    if (!MONGODB_URI) {
        log('[FATAL_DB_ERROR] MONGODB_URI is not set. Cannot connect to database.');
        return res.status(200).send('success'); // Still send success to Yipay
    }

    let client;
    try {
        client = new MongoClient(MONGODB_URI);
        await client.connect();
        log('[DB_OPERATION] Successfully connected to MongoDB.');
        const db = client.db(DB_NAME);
        const ordersCollection = db.collection('orders');

        // 4.1 查询订单
        log(`[DB_OPERATION] Querying order: ${out_trade_no}`);
        const order = await ordersCollection.findOne({ orderNo: out_trade_no });

        if (!order) {
            log(`[DB_VALIDATION_ERROR] Order ${out_trade_no} not found in database.`);
            // Potentially suspicious, but still send success to Yipay to avoid retries.
            return res.status(200).send('success');
        }
        log(`[DB_OPERATION] Found order: ${out_trade_no}, Status: ${order.status}, Amount: ${order.amount}`);

        // 4.2 检查订单状态 (防止重复处理)
        if (order.status === 'paid') {
            log(`[DB_VALIDATION_INFO] Order ${out_trade_no} has already been marked as paid. Ignoring duplicate callback.`);
            return res.status(200).send('success');
        }
        if (order.status !== 'pending') {
            log(`[DB_VALIDATION_WARNING] Order ${out_trade_no} status is "${order.status}", not "pending". Might be an issue or already processed differently.`);
             // Decide if to proceed or not based on your business logic for other statuses
            return res.status(200).send('success');
        }

        // 3. 金额校验 (回调中的 money 是字符串，需要转换为数字与数据库中的数字比较)
        const callbackAmount = parseFloat(money);
        // 数据库中的 order.amount 应该是创建时存的数字类型
        if (order.amount !== callbackAmount) {
            log(`[AMOUNT_MISMATCH_ERROR] Order ${out_trade_no} amount mismatch. DB: ${order.amount}, Callback: ${callbackAmount}.`);
            // This is a critical issue, investigate. Still send success to Yipay for now.
            return res.status(200).send('success');
        }
        log(`[AMOUNT_VALIDATION_SUCCESS] Amount matches for order ${out_trade_no}. DB: ${order.amount}, Callback: ${callbackAmount}`);
        
        // 4.3 更新订单状态为 'paid'
        log(`[DB_OPERATION] Updating order ${out_trade_no} status to 'paid'.`);
        const updateResult = await ordersCollection.updateOne(
            { orderNo: out_trade_no, status: 'pending' }, // Ensure we only update if still pending
            {
                $set: {
                    status: 'paid',
                    gatewayTradeNo: trade_no, // 保存易支付的交易号
                    paymentType: type,        // 保存支付方式
                    paidAt: new Date(),       // 记录支付时间
                    updatedAt: new Date()
                }
            }
        );

        if (updateResult.modifiedCount === 0 && updateResult.matchedCount > 0) {
             log(`[DB_OPERATION_WARNING] Order ${out_trade_no} was matched but not modified. It might have been updated by another process just before this one.`);
             // This implies it was no longer 'pending' when updateOne ran, could be a race condition.
             // Or status was already 'paid' but our earlier check missed it (less likely if checks are sequential).
             return res.status(200).send('success');
        } else if (updateResult.modifiedCount > 0) {
            log(`[DB_OPERATION_SUCCESS] Order ${out_trade_no} successfully updated to 'paid'.`);

            // --- 5. 生成并存储激活码 ---
            let generatedLicenseKey = null;
            try {
                if (!order.userEmail || !order.productId) {
                    log(`[LICENSE_ERROR] Missing userEmail or productId for order ${out_trade_no}. Cannot generate license.`);
                    // 即使无法生成激活码，也应该继续响应支付平台成功，避免重试。问题需要后续排查。
                } else {
                    generatedLicenseKey = generateLicense(order.userEmail, order.productId);
                    log(`[LICENSE_GENERATION_SUCCESS] Generated license key for order ${out_trade_no}: ${generatedLicenseKey}`);

                    const licenseUpdateResult = await ordersCollection.updateOne(
                        { orderNo: out_trade_no },
                        {
                            $set: {
                                licenseKey: generatedLicenseKey,
                                licenseGeneratedAt: new Date(),
                                updatedAt: new Date() // 也更新一下整体的updatedAt
                            }
                        }
                    );

                    if (licenseUpdateResult.modifiedCount > 0) {
                        log(`[DB_OPERATION_SUCCESS] License key for order ${out_trade_no} successfully stored in database.`);
                    } else {
                        // 如果订单状态已更新，但激活码存储失败，这是一个需要关注的问题
                        log(`[DB_OPERATION_ERROR] Failed to store license key for order ${out_trade_no}. Matched: ${licenseUpdateResult.matchedCount}, Modified: ${licenseUpdateResult.modifiedCount}`);
                        // 标记一下，虽然回调仍算成功，但激活码未成功保存
                    }
                }
            } catch (licenseError) {
                log(`[LICENSE_ERROR] Error during license generation or storage for order ${out_trade_no}: ${licenseError.message}`);
                console.error(licenseError); // 记录完整错误
                // 激活码生成/存储失败不应阻塞对支付平台的成功响应
            }
            
            // --- 6. 发送邮件 (如果激活码成功生成) ---
            try {
                if (generatedLicenseKey && order.userEmail) { // 确保有激活码和邮箱才发送
                    log(`[EMAIL_PREPARE] Preparing to send license email to ${order.userEmail} for order ${out_trade_no}.`);
                    const emailSent = await sendLicenseEmail(order.userEmail, generatedLicenseKey, out_trade_no);
                    if (emailSent) {
                        log(`[EMAIL_SUCCESS] License email for order ${out_trade_no} sent successfully (or at least attempted).`);
                        // 可选：在数据库中记录邮件发送成功状态。为避免增加回调处理时间，可以异步处理或标记后由定时任务处理。
                        // try {
                        //     await ordersCollection.updateOne({ orderNo: out_trade_no }, { $set: { emailSentAt: new Date(), emailSendStatus: 'success', updatedAt: new Date() } });
                        //     log(`[DB_OPERATION_SUCCESS] Marked email as sent for order ${out_trade_no}.`);
                        // } catch (dbUpdateError) {
                        //     log(`[DB_OPERATION_ERROR] Failed to mark email as sent for order ${out_trade_no}: ${dbUpdateError.message}`);
                        // }
                    } else {
                        log(`[EMAIL_FAILURE] License email sending failed for order ${out_trade_no}. Check logs from sendLicenseEmail function for error details.`);
                        // 可选：在数据库中记录邮件发送失败状态。
                        // try {
                        //     await ordersCollection.updateOne({ orderNo: out_trade_no }, { $set: { emailSendStatus: 'failed', updatedAt: new Date() } });
                        //     log(`[DB_OPERATION_SUCCESS] Marked email as failed for order ${out_trade_no}.`);
                        // } catch (dbUpdateError) {
                        //     log(`[DB_OPERATION_ERROR] Failed to mark email as failed for order ${out_trade_no}: ${dbUpdateError.message}`);
                        // }
                    }
                } else {
                    log(`[EMAIL_SKIP] Skipped sending email for order ${out_trade_no} due to missing license key or user email.`);
                }
            } catch (emailError) {
                log(`[EMAIL_EXCEPTION] Exception during email sending process for order ${out_trade_no}: ${emailError.message}`);
                console.error(emailError); // 记录完整错误
            }

        } else {
            log(`[DB_OPERATION_ERROR] Failed to update order ${out_trade_no} or order not found/not pending for update. Matched: ${updateResult.matchedCount}, Modified: ${updateResult.modifiedCount}`);
            return res.status(200).send('success');
        }

        log(`[WORKFLOW_SUCCESS] Order ${out_trade_no} processed successfully up to payment update. Responding success.`);
        res.status(200).send('success');

    } catch (dbError) {
        log(`[FATAL_DB_ERROR] Database operation failed for order ${out_trade_no}: ${dbError.message}`);
        console.error(dbError); // Log the full error stack for debugging
        // Even with DB error, send success to Yipay to avoid retries, but log it for investigation.
        res.status(200).send('success');
    } finally {
        if (client) {
            try {
                await client.close();
                log('[DB_OPERATION] MongoDB connection closed.');
            } catch (closeError) {
                log(`[DB_OPERATION_ERROR] Error closing MongoDB connection: ${closeError.message}`);
            }
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
  log(`[EMAIL_INFO] Attempting to send license email to: ${email} for order: ${orderNo} with key: ${licenseKey}`);

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