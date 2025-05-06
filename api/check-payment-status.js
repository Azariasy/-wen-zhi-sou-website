// api/check-payment-status.js
// 接收前端的GET请求，参数为内部订单号 (internalOrderNo)。
// 查询数据库中该订单的支付状态。
// 返回状态给前端 (例如: 'PENDING', 'PAID', 'FAILED')。

// 示例: 使用 Node.js (Vercel Serverless Function)

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed', message: 'Only GET requests are accepted.' });
  }

  try {
    const { orderNo } = req.query; // 从查询参数中获取订单号

    if (!orderNo) {
      return res.status(400).json({ error: 'Bad Request', message: 'Missing required query parameter: orderNo.' });
    }

    console.log('Checking payment status for order:', orderNo);

    // 1. 从您的数据库中查询订单状态
    //    这里是一个模拟的查询，您需要替换为对实际数据库的查询操作
    // const orderDetails = await getOrderFromDB(orderNo);
    
    // --- 模拟数据库查询 ---
    let mockStatus = 'PENDING';
    // 简单模拟：如果订单号包含特定数字，则认为已支付或失败
    if (orderNo.includes('7')) mockStatus = 'PAID';
    else if (orderNo.includes('0')) mockStatus = 'FAILED';
    
    const mockOrderDetails = {
        orderNo: orderNo,
        status: mockStatus, // 'PENDING', 'PAID', 'FAILED'
        // ... 其他订单信息
    };
    // --- 结束模拟 ---

    if (mockOrderDetails) {
      console.log(`Status for order ${orderNo}: ${mockOrderDetails.status}`);
      res.status(200).json({
        success: true,
        orderNo: mockOrderDetails.orderNo,
        status: mockOrderDetails.status, // 'PENDING', 'PAID', 'FAILED'
        // (可选) lastChecked: new Date().toISOString()
      });
    } else {
      console.warn(`Order ${orderNo} not found for status check.`);
      res.status(404).json({ success: false, error: 'Order Not Found' });
    }

  } catch (error) {
    console.error('Error in /api/check-payment-status:', error);
    res.status(500).json({ success: false, error: 'Internal Server Error', details: error.message });
  }
};

// 辅助函数: 从数据库获取订单 (需要您实现 - 可以与 payment-callback 中的共用)
// async function getOrderFromDB(orderNo) {
//   // ... 数据库查询逻辑 ...
//   // 示例:
//   // if (db.orders.findOne({ internalOrderNo: orderNo })) {
//   //   return db.orders.findOne({ internalOrderNo: orderNo });
//   // }
//   // return null;
//   // 模拟:
//   if (orderNo.startsWith("WZS-")) {
//       let status = 'PENDING';
//       if (orderNo.includes('7')) status = 'PAID';
//       else if (orderNo.includes('0')) status = 'FAILED';
//       return { orderNo: orderNo, status: status, email: 'simulated@example.com', productId: 'pro-yearly', price: 99 };
//   }
//   return null;
// } 