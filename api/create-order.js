// api/create-order.js - 检查文件是否可以被写入

// 先尝试导入 axios，查看是否能找到模块
// const axios = require('axios');

// 简化导出函数，只返回成功响应和正确的CORS头
export default async function handler(req, res) {
    // 先记录日志
    console.log('--- create-order function invoked ---');
    console.log('Request method:', req.method);
    
    // 设置通用CORS头部，允许来自GitHub Pages的请求
    res.setHeader('Access-Control-Allow-Origin', 'https://azariasy.github.io');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Allow-Credentials', 'true');

    // 处理预检请求
    if (req.method === 'OPTIONS') {
        console.log('Responding to OPTIONS preflight request');
        return res.status(204).end();
    }

    // 处理POST请求 - 简化版，只返回成功
    if (req.method === 'POST') {
        try {
            // 记录请求体，以便调试
            console.log('Request body:', req.body);
            
            // 不导入axios，直接返回成功响应
            return res.status(200).json({
                code: 0,
                msg: 'API endpoint working correctly',
                received: req.body,
                payUrl: 'https://example.com/test-payment' // 测试用支付URL
            });
        } catch (error) {
            console.error('Error in create-order API:', error);
            return res.status(500).json({ 
                code: 1, 
                msg: 'Server error', 
                error: error.message 
            });
        }
    } else {
        res.setHeader('Allow', ['POST', 'OPTIONS']);
        return res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}
