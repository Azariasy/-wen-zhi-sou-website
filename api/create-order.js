// api/create-order.js - 检查文件是否可以被写入

const { MongoClient } = require('mongodb');
const axios = require('axios');
const crypto = require('crypto');

// 从环境变量读取配置
const MONGODB_URI = process.env.MONGODB_URI;
const YIPAY_PID = process.env.PAYMENT_YIPAY_PID;
const YIPAY_KEY = process.env.PAYMENT_YIPAY_MD5_KEY;
const YIPAY_API_URL = process.env.YIPAY_API_URL; // 例如 'https://your-yipay-domain.com/submit.php'
const VERCEL_URL = process.env.VERCEL_URL; // Vercel 部署的 URL
const GITHUB_PAGES_URL = process.env.GITHUB_PAGES_URL; // GitHub Pages 网站 URL

// 辅助函数：生成MD5签名 (根据易支付文档调整)
function generateSign(params, apiKey) {
    const sortedKeys = Object.keys(params).sort();
    let signStr = '';
    for (const key of sortedKeys) {
        if (params[key] !== '' && params[key] !== undefined && params[key] !== null) {
            signStr += `${key}=${params[key]}&`;
        }
    }
    signStr += `key=${apiKey}`;
    return crypto.createHash('md5').update(signStr).digest('hex');
}

export default async function handler(req, res) {
    // CORS 处理
    // 注意：'https://azariasy.github.io' 应该替换为您的实际 GitHub Pages 域名
    // 或者从环境变量读取允许的源
    const allowedOrigin = process.env.ALLOWED_ORIGIN || 'https://azariasy.github.io';
    res.setHeader('Access-Control-Allow-Origin', allowedOrigin);
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization'); // 添加 Authorization 如果需要

    if (req.method === 'OPTIONS') {
        return res.status(204).end();
    }

    if (req.method === 'POST') {
        try {
            const { email, productId, amount, description, paymentType = 'alipay' } = req.body; // paymentType 可以由前端传递或默认

            // 1. 请求数据校验
            if (!email || !productId || !amount || !description) {
                return res.status(400).json({ code: 1, msg: '缺少必要的参数' });
            }
            const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
            if (!emailRegex.test(email)) {
                return res.status(400).json({ code: 1, msg: '邮箱格式不正确' });
            }
            if (isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
                return res.status(400).json({ code: 1, msg: '金额无效' });
            }

            // 2. 生成商户订单号
            const orderNo = `WZS${Date.now()}${Math.floor(Math.random() * 10000)}`;

            // 3. 准备调用易支付API的参数
            const notifyUrl = `${VERCEL_URL}/api/payment-callback`;
            const returnUrl = `${GITHUB_PAGES_URL}/purchase-success.html`; // 支付成功后的跳转页面

            const yipayParams = {
                pid: YIPAY_PID,
                type: paymentType, // 支付方式，如 alipay, wxpay
                out_trade_no: orderNo,
                notify_url: notifyUrl,
                return_url: returnUrl,
                name: description,
                money: parseFloat(amount).toFixed(2),
                sign_type: 'MD5',
            };
            yipayParams.sign = generateSign(yipayParams, YIPAY_KEY);

            // 4. 调用易支付API (具体请求方式和参数请参照易支付文档)
            // 这里假设易支付的 submit.php 接受 GET 请求并将参数附在 URL 上，然后重定向
            // 或者易支付直接返回支付二维码链接或HTML表单等
            let payUrl;
            try {
                // 通常易支付的 submit.php 是用来构建支付跳转链接的，而不是直接通过axios请求获得JSON响应
                // 这里的实现方式取决于易支付API的具体行为
                // 方式一: 如果易支付 submit.php 是GET请求并且直接跳转或返回支付URL
                const params = new URLSearchParams(yipayParams).toString();
                payUrl = `${YIPAY_API_URL}?${params}`;

                // 方式二: 如果易支付API需要POST请求并返回JSON (较少见于此类支付网关的跳转)
                // const yipayResponse = await axios.post(YIPAY_API_URL, yipayParams);
                // if (yipayResponse.data && yipayResponse.data.payUrl) { // 假设返回数据结构
                //     payUrl = yipayResponse.data.payUrl;
                // } else {
                //     console.error('易支付API响应格式不正确:', yipayResponse.data);
                //     return res.status(500).json({ code: 1, msg: '创建支付订单失败: 易支付响应错误' });
                // }

            } catch (yipayError) {
                console.error('调用易支付API失败:', yipayError.response ? yipayError.response.data : yipayError.message);
                return res.status(500).json({ code: 1, msg: '创建支付订单失败: 调用支付网关时出错' });
            }

            if (!payUrl) {
                 console.error('未能从易支付获取支付URL', yipayParams);
                 return res.status(500).json({ code: 1, msg: '创建支付订单失败: 未能获取支付链接' });
            }

            // 5. 存储订单到MongoDB
            let client;
            try {
                client = new MongoClient(MONGODB_URI);
                await client.connect();
                const db = client.db(); // 使用默认数据库或指定数据库名称
                const ordersCollection = db.collection('orders');

                const orderDocument = {
                    orderNo,
                    userEmail: email,
                    productId,
                    amount: parseFloat(amount),
                    description,
                    status: "pending", // 初始状态
                    paymentGateway: "yipay",
                    gatewayParams: yipayParams, // 保存请求易支付的参数，方便调试
                    createdAt: new Date(),
                    updatedAt: new Date(),
                    licenseKey: null,
                    licenseActivatedAt: null,
                    licenseDeviceId: null,
                };
                await ordersCollection.insertOne(orderDocument);
                console.log('订单已存入数据库:', orderNo);

            } catch (dbError) {
                console.error('数据库操作失败:', dbError);
                // 注意：如果数据库操作失败，但易支付订单已创建，需要有机制处理这种不一致性
                // 简单处理是返回错误，但更好的做法是记录下来，尝试补偿或提示用户联系客服
                return res.status(500).json({ code: 1, msg: '订单创建失败: 数据库错误' });
            } finally {
                if (client) {
                    await client.close();
                }
            }

            // 6. 返回支付URL给前端
            return res.status(200).json({ code: 0, msg: '订单创建成功，请准备支付', payUrl: payUrl });

        } catch (error) {
            console.error('创建订单API未知错误:', error);
            return res.status(500).json({ code: 1, msg: '服务器内部错误' });
        }
    } else {
        res.setHeader('Allow', ['POST', 'OPTIONS']);
        return res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}
