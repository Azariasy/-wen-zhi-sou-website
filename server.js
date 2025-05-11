const express = require('express');
const bodyParser = require('body-parser'); // To parse JSON request bodies

// 您的API处理逻辑 (假设它们是CommonJS模块)
const createOrderHandler = require('./api/create-order.js');
const paymentCallbackHandler = require('./api/payment-callback.js'); // 取消注释
// const checkPaymentStatusHandler = require('./api/check-payment-status.js');
const activateLicenseHandler = require('./api/activate-license.js'); // 新增：引入激活处理器

const app = express();
const PORT = process.env.PORT || 3000; // 您可以选择其他端口

// 中间件
app.use(bodyParser.json()); // 解析 application/json 类型的请求体
app.use(bodyParser.urlencoded({ extended: true })); // 解析 application/x-www-form-urlencoded 类型的请求体

// 日志中间件 (可选，但有助于调试)
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} ${req.ip}`); // 添加了IP地址记录
    // 记录请求体 (如果是POST/PUT等，且内容类型是JSON)
    if (req.body && Object.keys(req.body).length > 0 && req.get('Content-Type') === 'application/json') {
        console.log('Request Body:', JSON.stringify(req.body, null, 2));
    }
    next();
});

// API 路由
// 注意：createOrderHandler 已经包含了CORS头和OPTIONS预检请求的处理
app.post('/api/create-order', createOrderHandler);
app.options('/api/create-order', createOrderHandler); // 确保OPTIONS请求也由它处理

// 支付回调路由 (处理GET请求)
app.get('/api/payment-callback', paymentCallbackHandler); // 新增并明确为GET

// 新增：激活API路由
// 确保您的 activateLicenseHandler 模块能正确处理请求和响应
app.post('/api/activate-license', activateLicenseHandler);

// 示例：其他API路由 (如果需要)
// app.get('/api/check-payment-status', checkPaymentStatusHandler);

// 根路径的简单响应 (可选，用于测试服务器是否启动)
app.get('/', (req, res) => {
    res.send('API Server is running! 文智搜激活与支付服务已启动。'); // 修改了根路径的响应信息
});

// 404 错误处理中间件 (应放在所有具体路由之后，通用错误处理中间件之前)
app.use((req, res, next) => {
    // 如果到这里还没有匹配的路由，则认为是404
    // 注意：确保这个中间件不会捕获到由其他路由内部逻辑next(error)传递下来的错误
    if (!res.headersSent) { 
        res.status(404).json({ 
            success: false,
            message: `请求的资源未找到: ${req.method} ${req.originalUrl}` 
        });
    } else {
        next(); // 如果头已发送，则传递给下一个错误处理器（如果有）
    }
});

// 通用错误处理中间件 (这个中间件应该放在所有路由定义和特定错误处理之后)
app.use((err, req, res, next) => {
    console.error(`[${new Date().toISOString()}] Unhandled error for ${req.method} ${req.url}:`);
    console.error(err.stack || err); // 打印完整的错误栈或错误对象
    
    // 避免在已经发送响应后再发送
    if (res.headersSent) {
        return next(err); // 重要：如果头已发送，必须将错误传递给Express的默认错误处理器
    }
    
    res.status(err.status || 500).json({ // 如果错误对象有status属性，则使用它
        success: false,
        message: err.message || '服务器内部错误，请稍后重试或联系管理员。',
        // 在开发环境下可以考虑发送更详细的错误信息
        errorDetails: process.env.NODE_ENV === 'development' && err.stack ? err.stack.split('\n') : undefined
    });
});

app.listen(PORT, '0.0.0.0', () => { // 监听所有网络接口
    console.log(`文智搜 API 服务器已在端口 ${PORT} 上启动`);
    console.log(`本地访问: http://localhost:${PORT}`);
    console.log(`公网访问 (ECS防火墙/安全组配置后): http://<YOUR_ECS_PUBLIC_IP>:${PORT}`);
    console.log('已配置的API路由:');
    console.log('  POST /api/create-order');
    console.log('  OPTIONS /api/create-order');
    console.log('  GET /api/payment-callback');
    console.log('  POST /api/activate-license'); // 新增的路由
    console.log('  GET / (根路径测试)');
}); 