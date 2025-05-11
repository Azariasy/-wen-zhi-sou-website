module.exports = {
  apps : [{
    name   : "my-api-server",        // 您的应用名称，与 PM2 命令中使用的保持一致
    script : "./server.js",          // 您的 Node.js 应用入口文件，通常是 server.js 或 app.js
    cwd    : "C:\\api-server",       //  指定应用的工作目录，确保 PM2 在正确的路径下执行脚本
    watch  : false,                  // 是否启用文件监控并在文件更改时自动重启，生产环境通常设为 false
    max_memory_restart : "300M",   // 当应用占用内存超过300MB时自动重启
    env: {
      // --- 常用环境变量 ---
      "NODE_ENV": "production",         // 运行环境: 'production' 或 'development'

      // --- MongoDB 数据库配置 ---
      "MONGODB_URI": "mongodb+srv://wenzhisou_admin:YYM199055ggn@cluster0.wgowten.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", // 您的 MongoDB Atlas 连接字符串
      "DB_NAME": "wenzisou",              // 您的数据库名称

      // --- 易支付配置 ---
      "PAYMENT_YIPAY_PID": "14402",             // 您的易支付商户ID
      "PAYMENT_YIPAY_MD5_KEY": "3aeoc1ONN0N8tNDeWE8E8nN8OTAaDn01",     // 您的易支付 MD5 密钥
      "YIPAY_API_URL": "https://pay.myzfw.com", // 易支付API基础URL (如果不是默认的，请修改)

      // --- 激活码生成密钥 ---
      "LICENSE_SECRET": "aK3j8$Lp!7gCz#sX9@fH2*qW5&eR1^tY0(uI", // 用于生成激活码的强随机密钥

      // --- 邮件服务配置 (以通用 SMTP 为例) ---
      "EMAIL_SMTP_HOST": "smtp.qq.com",             // 例如: 'smtp.example.com' 或 'smtp.qq.com'
      "EMAIL_SMTP_PORT": "465",                          // 例如: 587 (TLS) 或 465 (SSL)
      "EMAIL_SMTP_SECURE": "true",                      // 如果端口是 465 (SSL) 则为 'true', 其他常见端口 (如587 STARTTLS) 为 'false'
      "EMAIL_SMTP_USER": "563625618@qq.com",         // 您的邮箱登录用户名
      "EMAIL_SMTP_PASS": "jduviwkvktjfbcag",         // 您的邮箱登录密码或应用专用密码
      "EMAIL_FROM_ADDRESS": "563625618@qq.com",    // 您希望邮件显示的发件人地址

      // --- 应用特定配置 ---
      "NOTIFY_URL_BASE": "https://yymwxx.cn", // 您的回调URL基础域名，例如 https://yourdomain.com
      // 您可以根据需要添加更多自定义环境变量
      // "ANOTHER_VARIABLE": "its_value"
    }
  }]
  // 如果您有部署相关的配置，可以添加到 deploy 部分
  // deploy : {
  //   production : {
  //     user : "your_ssh_user",
  //     host : "your_server_ip",
  //     ref  : "origin/main", // 或者您的主分支
  //     repo : "git@example.com:user/repo.git",
  //     path : "/var/www/production",
  //     "post-deploy" : "npm install && pm2 reload ecosystem.config.js --env production"
  //   }
  // }
}; 