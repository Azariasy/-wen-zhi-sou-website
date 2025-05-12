/**
 * 文智搜设备管理API
 * 用于列出已激活设备和解除设备激活
 */

const fs = require('fs');
const path = require('path');
const { MongoClient, ObjectId } = require('mongodb');

// --- 数据库连接信息 ---
const MONGODB_CONNECTION_URI = process.env.MONGODB_URI;
const DATABASE_NAME = process.env.DB_NAME || 'wenzisou';

// 日志函数
function log(type, message, data = null) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${type}] ${message}`;
  console.log(logMessage);
  if (data) {
    console.log(JSON.stringify(data, null, 2));
  }
  if (type === 'ERROR' || type === 'DEACTIVATION_SUCCESS' || type === 'DEACTIVATION_FAILED') {
    try {
      const logDir = path.join(__dirname, '../logs');
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      const logFile = path.join(logDir, `device-management-${new Date().toISOString().split('T')[0]}.log`);
      fs.appendFileSync(logFile, logMessage + (data ? `\n${JSON.stringify(data, null, 2)}` : '') + '\n');
    } catch (err) {
      console.error(`[${new Date().toISOString()}] [ERROR] Error writing to API log file: ${err.message}`);
    }
  }
}

/**
 * 列出许可证已激活的设备
 */
async function listDevices(req, res) {
  log('REQUEST', '收到列出设备请求', { query: req.query });
  
  const { licenseKey, deviceId } = req.query;
  
  if (!licenseKey || !deviceId) {
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
    const order = await db.collection('orders').findOne({ licenseKey });
    
    if (!order) {
      return res.status(404).json({
        success: false,
        message: '未找到此激活码关联的许可证信息。'
      });
    }
    
    // 确保当前设备有权限查看设备列表
    const activated_devices = order.activated_devices || [];
    if (!activated_devices.includes(deviceId) && order.licenseDeviceId !== deviceId) {
      return res.status(403).json({
        success: false,
        message: '无权限查看此许可证的设备列表。'
      });
    }
    
    // 格式化设备信息
    const deviceInfo = activated_devices.map((deviceId, index) => {
      const isCurrentDevice = deviceId === req.query.deviceId;
      return {
        id: deviceId,
        name: isCurrentDevice ? '当前设备' : `设备 ${index + 1}`,
        activationDate: order.licenseActivatedAt || order.updatedAt,
        isCurrentDevice
      };
    });
    
    return res.status(200).json({
      success: true,
      license: {
        key: licenseKey.substring(0, 4) + '****', // 只显示前4位，其余掩盖
        maxDevices: order.max_devices || 1,
        currentDevices: activated_devices.length,
        purchaseDate: order.paidAt || order.createdAt,
        email: order.userEmail
      },
      devices: deviceInfo
    });
    
  } catch (error) {
    log('ERROR', `列出设备时出错: ${error.message}`, { stack: error.stack });
    return res.status(500).json({
      success: false,
      message: '处理请求时发生服务器内部错误，请稍后重试。'
    });
  } finally {
    if (client) {
      await client.close();
    }
  }
}

/**
 * 解除设备激活
 */
async function deactivateDevice(req, res) {
  log('REQUEST', '收到解除设备激活请求', { body: req.body });
  
  const { licenseKey, deviceId, targetDeviceId } = req.body;
  
  if (!licenseKey || !deviceId || !targetDeviceId) {
    return res.status(400).json({
      success: false,
      message: '请求参数不完整，需要提供licenseKey、deviceId和targetDeviceId。'
    });
  }
  
  // 不允许解除当前设备，应该使用专门的注销功能
  if (deviceId === targetDeviceId) {
    return res.status(400).json({
      success: false,
      message: '无法解除当前设备，请使用注销功能。'
    });
  }
  
  let client;
  try {
    client = new MongoClient(MONGODB_CONNECTION_URI);
    await client.connect();
    
    const db = client.db(DATABASE_NAME);
    const order = await db.collection('orders').findOne({ licenseKey });
    
    if (!order) {
      return res.status(404).json({
        success: false,
        message: '未找到此激活码关联的许可证信息。'
      });
    }
    
    // 确保当前设备有权限管理设备列表
    const activated_devices = order.activated_devices || [];
    if (!activated_devices.includes(deviceId) && order.licenseDeviceId !== deviceId) {
      return res.status(403).json({
        success: false,
        message: '无权限管理此许可证的设备列表。'
      });
    }
    
    // 检查目标设备是否在激活列表中
    if (!activated_devices.includes(targetDeviceId)) {
      return res.status(400).json({
        success: false,
        message: '指定设备未在此许可证的激活列表中。'
      });
    }
    
    // 执行解除激活
    const updateResult = await db.collection('orders').updateOne(
      { licenseKey },
      { $pull: { activated_devices: targetDeviceId } }
    );
    
    if (updateResult.modifiedCount === 0) {
      log('DEACTIVATION_FAILED', '解除设备激活失败', { licenseKey, targetDeviceId });
      return res.status(500).json({
        success: false,
        message: '解除设备激活失败，请稍后重试。'
      });
    }
    
    // 获取更新后的订单信息
    const updatedOrder = await db.collection('orders').findOne({ licenseKey });
    const updatedDevices = updatedOrder.activated_devices || [];
    
    log('DEACTIVATION_SUCCESS', '设备已成功解除激活', { 
      licenseKey, 
      targetDeviceId,
      remainingDevices: updatedDevices.length 
    });
    
    return res.status(200).json({
      success: true,
      message: '设备已成功解除激活。',
      maxDevices: order.max_devices || 1,
      currentDevices: updatedDevices.length
    });
    
  } catch (error) {
    log('ERROR', `解除设备激活时出错: ${error.message}`, { stack: error.stack });
    return res.status(500).json({
      success: false,
      message: '处理请求时发生服务器内部错误，请稍后重试。'
    });
  } finally {
    if (client) {
      await client.close();
    }
  }
}

/**
 * API路由处理器
 */
module.exports = async (req, res) => {
  // 处理OPTIONS预检请求
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }
  
  // 处理CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  // 根据请求方法和路径路由到相应处理函数
  if (req.method === 'GET') {
    return await listDevices(req, res);
  } else if (req.method === 'POST') {
    return await deactivateDevice(req, res);
  } else {
    return res.status(405).json({
      success: false,
      message: '不支持的请求方法。'
    });
  }
}; 