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
      const logFile = path.join(logDir, `activation-${new Date().toISOString().split('T')[0]}.log`);
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
 * 检查设备是否已激活，以及处理多设备激活逻辑
 * @param {Array} activatedDevices 已激活的设备ID数组
 * @param {string} deviceId 当前要激活的设备ID
 * @param {number} maxDevices 最大允许激活的设备数
 * @returns {Object} 包含是否可以激活与原因的对象 {canActivate, reason, alreadyActivated}
 */
function isDeviceAlreadyActivated(activatedDevices = [], deviceId, maxDevices = 1) {
  // 检查设备ID是否已经在激活列表中
  const alreadyActivated = activatedDevices.includes(deviceId);
  
  // 如果设备已经激活，直接允许激活
  if (alreadyActivated) {
    return {
      canActivate: true,
      reason: '此设备已经激活过，重新激活成功。',
      alreadyActivated: true
    };
  }
  
  // 如果尚未达到最大设备数，允许激活
  if (activatedDevices.length < maxDevices) {
    return {
      canActivate: true,
      reason: '新设备激活成功。',
      alreadyActivated: false
    };
  }
  
  // 如果已达到最大设备数，拒绝激活
  return {
    canActivate: false,
    reason: `已达到最大激活设备数 (${maxDevices})，无法在新设备上激活。请先在其他设备上注销后再尝试。`,
    alreadyActivated: false
  };
}

/**
 * 记录激活信息到数据库
 * @param {Object} db 数据库连接
 * @param {string} licenseKey 许可证密钥
 * @param {string} deviceId 设备ID
 * @returns {Promise<Object>} 更新结果
 */
async function recordActivation(db, licenseKey, deviceId) {
  const now = new Date();
  
  // 使用 $addToSet 来添加不重复的设备ID
  const updateResult = await db.collection('orders').updateOne(
    { licenseKey },
    { 
      $set: { 
        // 如果是首次激活，设置激活信息
        licenseActivatedAt: { $exists: true } ? undefined : now,
        updatedAt: now
      },
      $addToSet: { activated_devices: deviceId }
    }
  );
  
  return updateResult;
}

/**
 * 处理激活请求
 * @param {object} req - Express请求对象
 * @param {object} res - Express响应对象
 */
module.exports = async (req, res) => {
  // 处理OPTIONS预检请求
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }
  
  // 只允许POST请求
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      message: '不支持的HTTP方法。请使用POST请求。'
    });
  }
  
  // 处理CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // 获取请求体
  const { licenseKey, deviceId } = req.body;
  
  // 验证必要参数
  if (!licenseKey || !deviceId) {
    log('ERROR', '请求参数不完整', { licenseKey: !!licenseKey, deviceId: !!deviceId });
    return res.status(400).json({
      success: false,
      message: '请求参数不完整，需要提供licenseKey和deviceId。'
    });
  }
  
  let client;
  try {
    client = new MongoClient(MONGODB_CONNECTION_URI);
    await client.connect();
    
    const db = client.db(DATABASE_NAME);
    
    // 查找许可证
    const order = await db.collection('orders').findOne({ licenseKey });
    
    // 如果找不到许可证
    if (!order) {
      log('ACTIVATION_FAILED', '激活码无效', { licenseKey, deviceId });
      return res.status(404).json({
        success: false,
        message: '激活码无效。请检查输入是否正确或联系客服。'
      });
    }
    
    // 检查是否已支付
    if (order.status !== 'paid') {
      log('ACTIVATION_FAILED', '激活码未支付', { licenseKey, deviceId, orderId: order._id });
      return res.status(400).json({
        success: false,
        message: '此激活码尚未完成支付，无法激活。'
      });
    }
    
    // 获取订单支持的最大设备数
    const maxDevices = order.max_devices || 1; // 默认为1
    
    // 检查已激活设备列表
    const activatedDevices = order.activated_devices || [];
    
    // 检查设备是否已经激活或可以激活
    const deviceActivationCheck = isDeviceAlreadyActivated(activatedDevices, deviceId, maxDevices);
    
    if (!deviceActivationCheck.canActivate) {
      log('ACTIVATION_FAILED', '设备数量超限', { 
        licenseKey, 
        deviceId, 
        currentDeviceCount: activatedDevices.length,
        maxDevices, 
        reason: deviceActivationCheck.reason 
      });
      
      return res.status(400).json({
        success: false,
        message: deviceActivationCheck.reason,
        currentDevices: activatedDevices.length,
        maxDevices
      });
    }
    
    // 记录激活信息
    if (!deviceActivationCheck.alreadyActivated) {
      await recordActivation(db, licenseKey, deviceId);
      log('ACTIVATION_SUCCESS', '新设备已成功激活', { 
        licenseKey, 
        deviceId, 
        orderId: order._id, 
        newDeviceCount: activatedDevices.length + 1,
        maxDevices
      });
    } else {
      log('ACTIVATION_SUCCESS', '已激活设备重新激活', { 
        licenseKey, 
        deviceId, 
        orderId: order._id, 
        deviceCount: activatedDevices.length,
        maxDevices
      });
    }
    
    // 获取更新后的订单信息
    const updatedOrder = await db.collection('orders').findOne({ licenseKey });
    const updatedDevices = updatedOrder.activated_devices || [];
    
    // 返回成功响应
    return res.status(200).json({
      success: true,
      message: deviceActivationCheck.alreadyActivated
        ? '设备已重新激活成功。'
        : '设备成功激活。',
      userEmail: order.userEmail,
      productId: order.productId,
      activationDate: order.licenseActivatedAt || order.updatedAt,
      purchaseDate: order.paidAt || order.createdAt,
      maxDevices,
      activatedDevices: updatedDevices,
      currentDevices: updatedDevices.length,
      alreadyActivated: deviceActivationCheck.alreadyActivated
    });
    
  } catch (error) {
    log('ERROR', `激活过程中出错: ${error.message}`, { stack: error.stack });
    return res.status(500).json({
      success: false,
      message: '激活过程中发生服务器内部错误，请稍后重试。'
    });
  } finally {
    if (client) {
      await client.close();
    }
  }
}; 