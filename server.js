const express = require('express');
const bodyParser = require('body-parser'); // To parse JSON request bodies

// 您的API处理逻辑 (假设它们是CommonJS模块)
const createOrderHandler = require('./api/create-order.js');
// 如果有其他API，也类似地引入:
// const paymentCallbackHandler = require('./api/payment-callback.js');
// const checkPaymentStatusHandler = require('./api/check-payment-status.js');

const app = express();
const PORT = process.env.PORT || 3000; // 您可以选择其他端口

// 中间件
app.use(bodyParser.json()); // 解析 application/json 类型的请求体
app.use(bodyParser.urlencoded({ extended: true })); // 解析 application/x-www-form-urlencoded 类型的请求体

// 日志中间件 (可选，但有助于调试)
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
});

// API 路由
// 注意：createOrderHandler 已经包含了CORS头和OPTIONS预检请求的处理
app.post('/api/create-order', createOrderHandler);
app.options('/api/create-order', createOrderHandler); // 确保OPTIONS请求也由它处理

// 示例：其他API路由 (如果需要)
// app.all('/api/payment-callback', paymentCallbackHandler); // .all 可以处理GET和POST
// app.get('/api/check-payment-status', checkPaymentStatusHandler);

// 根路径的简单响应 (可选，用于测试服务器是否启动)
app.get('/', (req, res) => {
    res.send('API Server is running!');
});

// 错误处理中间件 (可选，但推荐)
app.use((err, req, res, next) => {
    console.error("Unhandled error:", err.stack);
    res.status(500).send('Something broke!');
});

app.listen(PORT, '0.0.0.0', () => { // 监听所有网络接口
    console.log(`API server listening on port ${PORT}`);
    console.log(`Access locally: http://localhost:${PORT}`);
    console.log(`Access publicly (after firewall/SG config): http://<YOUR_ECS_PUBLIC_IP>:${PORT}`);
}); 