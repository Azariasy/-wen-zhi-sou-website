// api/create-order.js - 使用CommonJS格式

// 使用CommonJS模块格式
module.exports = async (req, res) => {
    // 先记录日志
    console.log('--- create-order function invoked ---');
    console.log('Request method:', req.method);
    console.log('Request origin:', req.headers.origin);
    
    // 设置CORS头 - 允许来自GitHub Pages的请求
    res.setHeader('Access-Control-Allow-Origin', 'https://azariasy.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Date, X-Api-Version');
    
    // 预检请求处理
    if (req.method === 'OPTIONS') {
        console.log('Responding to OPTIONS preflight request');
        res.status(204).end();
        return;
    }

    // 处理POST请求 - 最简化版本
    if (req.method === 'POST') {
        try {
            // 记录请求体，以便调试
            console.log('Request body:', req.body);
            
            // 返回一个简单的成功响应
            res.status(200).json({
                code: 0,
                msg: 'API endpoint working correctly - CORS test',
                received: req.body || {},
                payUrl: 'https://example.com/test-payment' // 测试用支付URL
            });
        } catch (error) {
            console.error('Error in create-order API:', error);
            res.status(500).json({ 
                code: 1, 
                msg: 'Server error', 
                error: error.message || 'Unknown error'
            });
        }
    } else {
        // 其他HTTP方法
        res.setHeader('Allow', ['POST', 'OPTIONS']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
};
