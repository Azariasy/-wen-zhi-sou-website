/**
 * 文智搜软件激活API
 * 处理激活请求，验证激活码，并返回激活结果
 */

const fs = require('fs');
const path = require('path');
// const crypto = require('crypto'); // 激活码生成/校验可能需要，但当前主要逻辑是查库
const { MongoClient, ObjectId } = require('mongodb');

// --- 数据库连接信息 ---
// 优先从环境变量读取，这些应该在 ecosystem.config.js 中定义
const MONGODB_CONNECTION_URI = process.env.MONGODB_URI;
const DATABASE_NAME = process.env.DB_NAME || 'wenzisou'; // ecosystem.config.js 中是 'wenzisou'

// 日志函数
function log(type, message, data = null) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${type}] ${message}`;
  console.log(logMessage);
  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }
  if (type === 'ERROR' || type === 'ACTIVATION_SUCCESS' || type === 'ACTIVATION_FAILED') {
    try {
      const logDir = path.join(__dirname, '../logs'); // 假设日志在项目根目录的 logs 文件夹下
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      const logFile = path.join(logDir, `activation-api-${new Date().toISOString().split('T')[0]}.log`);
      fs.appendFileSync(logFile, logMessage + (data ? `\n${JSON.stringify(data, null, 2)}` : '') + '\n');
    } catch (err) {
      console.error(`[${new Date().toISOString()}] [ERROR] Error writing to API log file: ${err.message}`);
    }
  }
}

// 预先检查关键环境变量
if (!MONGODB_CONNECTION_URI) {
  log('CRITICAL_ERROR', '环境变量 MONGODB_URI 未设置。API将无法连接数据库并处理请求。');
}
if (!DATABASE_NAME) { // 虽然有默认值，但最好检查一下
  log('WARNING', '环境变量 DB_NAME 未设置，将使用默认数据库名称: ' + DATABASE_NAME);
}

/**
 * 验证激活码的有效性
 * @param {string} licenseKey - 用户提供的激活码
 * @param {object} dbClient - MongoDB客户端连接
 * @returns {Promise<object>} - 验证结果
 */
async function validateLicenseKey(licenseKey, dbClient) {
  log('LICENSE_VALIDATION', `开始验证激活码: ${licenseKey}`);
  try {
    const db = dbClient.db(DATABASE_NAME); // 使用从环境变量获取或默认的数据库名
    // const licensesCollection = db.collection('licenses'); // 确保集合名称正确，文档是 'orders'
    const ordersCollection = db.collection('orders'); // 根据文档，激活码信息在 orders 集合

    // 根据技术方案文档，我们应该查 orders 集合中的 licenseKey
    // const license = await licensesCollection.findOne({ licenseKey }); // 如果有单独的 licenses 集合
    const orderWithLicense = await ordersCollection.findOne({ licenseKey: licenseKey });

    if (!orderWithLicense) {
      log('LICENSE_VALIDATION_FAILED', '激活码不存在于orders集合');
      return { valid: false, message: '无效的激活码，请检查输入是否正确。' };
    }

    log('LICENSE_FOUND', '在orders集合找到匹配的激活码', { orderId: orderWithLicense._id, licenseKey: orderWithLicense.licenseKey });

    // 检查订单状态是否已支付
    if (orderWithLicense.status !== 'paid') {
        log('LICENSE_VALIDATION_FAILED', '关联订单未完成支付或状态异常', { orderId: orderWithLicense._id, status: orderWithLicense.status });
        return { valid: false, message: '此激活码关联的订单尚未完成支付或状态异常。' };
    }
    
    log('LICENSE_VALIDATION_SUCCESS', '激活码初步验证成功 (存在且订单已支付)', {
      orderId: orderWithLicense._id,
      userEmail: orderWithLicense.userEmail,
      productId: orderWithLicense.productId
    });

    return {
      valid: true,
      licenseDetails: orderWithLicense, // 返回整个订单/许可证详情
      message: '激活码验证成功'
    };
  } catch (error) {
    log('ERROR', `验证激活码时出错: ${error.message}`, { stack: error.stack });
    return { valid: false, message: '验证激活码时发生服务器内部错误。' };
  }
}

/**
 * 记录设备激活信息
 * @param {string} orderId - 订单ID
 * @param {string} deviceId - 设备ID
 * @param {object} dbClient - MongoDB客户端连接
 * @returns {Promise<boolean>} - 是否成功记录
 */
async function recordActivation(orderId, deviceId, dbClient) {
  log('ACTIVATION_RECORD', `记录设备激活信息到orders集合`, { orderId, deviceId });
  try {
    const db = dbClient.db(DATABASE_NAME);
    const ordersCollection = db.collection('orders');

    const updateResult = await ordersCollection.updateOne(
      { _id: new ObjectId(orderId) },
      {
        $set: {
          licenseDeviceId: deviceId,
          licenseActivatedAt: new Date(),
          licenseStatus: 'active', // 根据您的状态定义
          updatedAt: new Date()
        }
      }
    );

    if (updateResult.modifiedCount === 1) {
      log('ACTIVATION_RECORD_SUCCESS', '设备激活信息已成功更新到orders记录', { orderId });
      return true;
    } else {
      log('ACTIVATION_RECORD_FAILED', '更新orders记录失败，可能orderId不存在或未找到匹配项', { orderId, matchedCount: updateResult.matchedCount });
      return false;
    }
  } catch (error) {
    log('ERROR', `记录设备激活时出错: ${error.message}`, { stack: error.stack });
    return false;
  }
}

/**
 * 检查设备是否已激活过此激活码
 * @param {object} licenseDetails - 激活码详情
 * @param {string} deviceId - 设备ID
 * @returns {Promise<boolean>} - 设备是否已激活过
 */
async function isDeviceAlreadyActivated(licenseDetails, deviceId /*, dbClient */) {
  // licenseDetails 是从 validateLicenseKey 返回的 orderWithLicense 对象
  if (licenseDetails.licenseDeviceId && licenseDetails.licenseDeviceId === deviceId) {
    log('DEVICE_ALREADY_ACTIVATED', '此设备已使用该激活码激活过', { licenseKey: licenseDetails.licenseKey, deviceId });
    return true;
  }
  if (licenseDetails.licenseDeviceId && licenseDetails.licenseDeviceId !== deviceId) {
    log('LICENSE_USED_OTHER_DEVICE', '该激活码已在其他设备上激活', { licenseKey: licenseDetails.licenseKey, existingDeviceId: licenseDetails.licenseDeviceId, requestedDeviceId: deviceId });
    return 'other_device'; // 返回特殊值表示被其他设备占用
  }
  return false; // 未激活或未绑定设备
}

/**
 * 处理激活请求
 * @param {object} req - Express请求对象
 * @param {object} res - Express响应对象
 */
module.exports = async (req, res) => {
  log('REQUEST', '收到激活请求', { body: req.body, ip: req.ip });

  if (!MONGODB_CONNECTION_URI) {
    log('ERROR', '由于MONGODB_URI未配置，无法处理激活请求。');
    return res.status(500).json({
      success: false,
      message: '服务器配置错误，激活服务暂时不可用，请联系管理员。'
    });
  }

  if (!req.body || !req.body.licenseKey || !req.body.deviceId) {
    log('VALIDATION_ERROR', '请求参数不完整', { body: req.body });
    return res.status(400).json({ success: false, message: '请求参数不完整，需要提供licenseKey和deviceId。' });
  }

  const { licenseKey, deviceId } = req.body;

  let client;
  try {
    log('DB_CONNECT', '正在连接数据库 (MongoDB Atlas)...', { uri_type: typeof MONGODB_CONNECTION_URI });
    client = new MongoClient(MONGODB_CONNECTION_URI);
    await client.connect();
    log('DB_CONNECT_SUCCESS', '数据库连接成功');

    const validationResult = await validateLicenseKey(licenseKey, client);

    if (!validationResult.valid) {
      log('ACTIVATION_FAILED', '激活失败 - 激活码验证未通过', { licenseKey, deviceId, message: validationResult.message });
      return res.status(400).json({ success: false, message: validationResult.message });
    }

    const { licenseDetails } = validationResult; // 这是 orders 集合中的文档

    const activationStatus = await isDeviceAlreadyActivated(licenseDetails, deviceId);

    if (activationStatus === true) { // 已在本设备激活
      log('ACTIVATION_INFO', '设备已经激活过此激活码', { licenseKey, deviceId, orderId: licenseDetails._id });
      return res.status(200).json({
        success: true,
        message: '此设备已成功激活，无需重复操作。',
        userEmail: licenseDetails.userEmail,
        productId: licenseDetails.productId,
        purchaseDate: licenseDetails.paidAt || licenseDetails.createdAt, // 使用 paidAt
        activationDate: licenseDetails.licenseActivatedAt,
        alreadyActivated: true
      });
    } else if (activationStatus === 'other_device') { // 已在其他设备激活
       log('ACTIVATION_FAILED', '激活码已在其他设备使用', { licenseKey, deviceId, orderId: licenseDetails._id });
       return res.status(409).json({ // 409 Conflict
         success: false,
         message: '激活失败：此激活码已在其他设备上使用。如需更换设备，请联系客服。'
       });
    }

    // 如果 activationStatus 为 false，表示可以进行新的激活
    const recordResult = await recordActivation(licenseDetails._id, deviceId, client);

    if (!recordResult) {
      log('ACTIVATION_ERROR', '记录激活信息失败', { licenseKey, deviceId });
      return res.status(500).json({ success: false, message: '激活过程中发生错误，请稍后重试。' });
    }

    log('ACTIVATION_SUCCESS', '激活成功', {
      licenseKey, deviceId, orderId: licenseDetails._id, userEmail: licenseDetails.userEmail
    });

    return res.status(200).json({
      success: true,
      message: '激活成功！感谢您购买文智搜专业版。',
      userEmail: licenseDetails.userEmail,
      productId: licenseDetails.productId,
      purchaseDate: licenseDetails.paidAt || licenseDetails.createdAt,
      activationDate: new Date() // 当前激活时间
    });

  } catch (error) {
    log('ERROR', `处理激活请求时发生意外错误: ${error.message}`, { stack: error.stack });
    // 检查是否是数据库连接相关的错误
    if (error.message && (error.message.toLowerCase().includes('econnrefused') || error.message.toLowerCase().includes('timeout')) && error.message.toLowerCase().includes('mongodb')) {
        return res.status(503).json({ success: false, message: '无法连接到激活数据库，请稍后重试或联系管理员。'});
    }
    return res.status(500).json({ success: false, message: '处理激活请求时发生服务器内部错误，请稍后重试。' });
  } finally {
    if (client) {
      try {
        await client.close();
        log('DB_DISCONNECT', '数据库连接已关闭');
      } catch (err) {
        log('ERROR', `关闭数据库连接时出错: ${err.message}`);
      }
    }
  }
}; 