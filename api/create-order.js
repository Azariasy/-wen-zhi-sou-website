// api/create-order.js - 使用CommonJS格式

const { MongoClient } = require('mongodb');
const axios = require('axios');
const crypto = require('crypto');

// 从环境变量读取配置 (这些需要在ECS服务器上设置)
const MONGODB_URI = process.env.MONGODB_URI;
const YIPAY_PID = process.env.PAYMENT_YIPAY_PID;
const YIPAY_KEY = process.env.PAYMENT_YIPAY_MD5_KEY;
const YIPAY_API_URL = process.env.YIPAY_API_URL;
const FRONTEND_SUCCESS_URL = process.env.FRONTEND_SUCCESS_URL || 'https://azariasy.github.io/-wen-zhi-sou-website/purchase-success.html'; // 前端支付成功跳转页

// 辅助函数：生成MD5签名
function generateSign(params, apiKey) {
    const sortedKeys = Object.keys(params).sort();
    let signStr = '';
    for (const key of sortedKeys) {
        if (params[key] !== '' && params[key] !== undefined && params[key] !== null && key !== 'sign' && key !== 'sign_type') {
            signStr += `${key}=${params[key]}&`;
        }
    }
    if (signStr.endsWith('&')) {
        signStr = signStr.slice(0, -1);
    }
    signStr = `${signStr}${apiKey}`;
    return crypto.createHash('md5').update(signStr).digest('hex');
}

module.exports = async (req, res) => {
    console.log(`--- create-order function invoked (Full Logic) ---`);
    console.log(`Request method: ${req.method}`);
    console.log(`Request origin: ${req.headers.origin}`);
    
    res.setHeader('Access-Control-Allow-Origin', 'https://azariasy.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Date, X-Api-Version');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    
    if (req.method === 'OPTIONS') {
        console.log('Responding to OPTIONS preflight request');
        return res.status(204).end();
    }

    if (req.method === 'POST') {
        console.log('Request body:', req.body);
        try {
            const { email, productId, amount, description, paymentType = 'alipay' } = req.body;

            if (!MONGODB_URI || !YIPAY_PID || !YIPAY_KEY || !YIPAY_API_URL) {
                console.error('关键环境变量未配置!');
                return res.status(500).json({ code: 1, msg: '服务器配置错误，请联系管理员' });
            }
            
            if (!email || !productId || !amount || !description) {
                return res.status(400).json({ code: 1, msg: '缺少必要的参数' });
            }
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            const trimmedEmail = email.trim(); // 先去除首尾空格
            console.log(`收到的原始 email: "${email}"`); // 记录原始email
            console.log(`去除空格后的 email: "${trimmedEmail}"`); // 记录处理后的email
            console.log(`使用的正则表达式: ${emailRegex.toString()}`); // 记录正则表达式本身

            if (!emailRegex.test(trimmedEmail)) { // 使用 trimmedEmail 进行测试
                console.error(`邮箱格式校验失败: "${trimmedEmail}" 未通过正则 ${emailRegex.toString()}`);
                return res.status(400).json({ code: 1, msg: '邮箱格式不正确' });
            }
            if (isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
                return res.status(400).json({ code: 1, msg: '金额无效' });
            }

            const orderNo = `WZS${Date.now()}${Math.floor(Math.random() * 10000)}`;
            const notifyUrl = `https://yymwxx.cn/api/payment-callback`;
            const returnUrl = FRONTEND_SUCCESS_URL;

            const yipayParams = {
                pid: YIPAY_PID,
                type: paymentType,
                out_trade_no: orderNo,
                notify_url: notifyUrl,
                return_url: returnUrl,
                name: description,
                money: parseFloat(amount).toFixed(2),
            };
            const paramsForSign = { ...yipayParams };
            yipayParams.sign = generateSign(paramsForSign, YIPAY_KEY);
            yipayParams.sign_type = 'MD5';

            console.log("易支付请求参数 (带签名):", yipayParams);

            const yipayQueryString = new URLSearchParams(yipayParams).toString();
            const payUrl = `${YIPAY_API_URL}?${yipayQueryString}`;
            console.log("生成的易支付URL:", payUrl);
            
            let client;
            try {
                client = new MongoClient(MONGODB_URI);
                await client.connect();
                console.log("成功连接到MongoDB");
                const db = client.db();
                const ordersCollection = db.collection('orders');

                const orderDocument = {
                    orderNo,
                    userEmail: email,
                    productId,
                    amount: parseFloat(amount),
                    description,
                    status: "pending",
                    paymentGateway: "yipay",
                    gatewayParamsChecksum: crypto.createHash('md5').update(JSON.stringify(yipayParams)).digest('hex'),
                    createdAt: new Date(),
                    updatedAt: new Date(),
                    licenseKey: null,
                };
                await ordersCollection.insertOne(orderDocument);
                console.log('订单已存入数据库:', orderNo);

            } catch (dbError) {
                console.error('数据库操作失败:', dbError);
                return res.status(500).json({ code: 1, msg: '订单创建失败: 数据库错误' });
            } finally {
                if (client) {
                    await client.close();
                    console.log("MongoDB连接已关闭");
                }
            }

            return res.status(200).json({ code: 0, msg: '订单创建成功，请准备支付', payUrl: payUrl });

        } catch (error) {
            console.error('创建订单API未知错误:', error);
            return res.status(500).json({ code: 1, msg: '服务器内部错误', error: error.message });
        }
    } else {
        res.setHeader('Allow', ['POST', 'OPTIONS']);
        return res.status(405).end(`Method ${req.method} Not Allowed`);
    }
};
