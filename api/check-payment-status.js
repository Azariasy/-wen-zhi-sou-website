// api/check-payment-status.js
// 接收前端的GET请求，参数为内部订单号 (internalOrderNo)。
// 查询数据库中该订单的支付状态。
// 返回状态给前端 (例如: 'PENDING', 'PAID', 'FAILED')。

// 示例: 使用 Node.js (Vercel Serverless Function)
import clientPromise from '../lib/mongodb'; // 导入数据库连接

module.exports = async (req, res) => {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed', message: 'Only GET requests are accepted.' });
  }

  let client; // Define client here to be accessible in finally

  try {
    const { orderNo } = req.query; // 从查询参数中获取订单号

    if (!orderNo) {
      return res.status(400).json({ error: 'Bad Request', message: 'Missing required query parameter: orderNo.' });
    }

    console.log('Checking payment status for order:', orderNo);

    // 1. 从您的数据库中查询订单状态
    client = await clientPromise;
    const db = client.db("wenzhisouDB"); // 使用您的数据库名称
    const ordersCollection = db.collection("orders"); // 使用您的集合名称

    const orderDetails = await ordersCollection.findOne({ internalOrderNo: orderNo });

    if (orderDetails) {
      console.log(`Status for order ${orderNo}: ${orderDetails.status}`);
      res.status(200).json({
        success: true,
        orderNo: orderDetails.internalOrderNo, // Use internalOrderNo from DB document
        status: orderDetails.status,
        // (可选) lastChecked: new Date().toISOString()
      });
    } else {
      console.warn(`Order ${orderNo} not found for status check.`);
      res.status(404).json({ success: false, error: 'Order Not Found' });
    }

  } catch (error) {
    console.error('Error in /api/check-payment-status:', error);
    res.status(500).json({ success: false, error: 'Internal Server Error', details: error.message });
  } finally {
    if (client) {
      await client.close();
    }
  }
};

// 辅助函数: 从数据库获取订单 (需要您实现 - 可以与 payment-callback 中的共用)
// async function getOrderFromDB(orderNo) {
//   // ... 数据库查询逻辑 ...
//   // 示例:
//   // const client = await clientPromise;
//   // const db = client.db("wenzhisouDB");
//   // const order = await db.collection("orders").findOne({ internalOrderNo: orderNo });
//   // await client.close();
//   // return order;
// } 