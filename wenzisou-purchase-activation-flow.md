# WenZhiSou - 购买与激活流程开发文档

## 1. 概述

本文档详细描述了文智搜（WenZhiSou）产品从用户发起购买请求到接收激活码并完成激活的完整流程。旨在为开发人员提供清晰的指引，方便理解、维护和扩展相关功能。

## 2. 系统架构概览

核心流程涉及以下组件：

*   **前端用户界面 (Website)**: 用户在此选择产品、填写信息并发起支付。
*   **后端 API 服务器 (Node.js - 部署于阿里云ECS)**: 处理购买请求、与支付网关交互、处理支付回调、生成激活码、与数据库交互、发送邮件。
*   **支付网关 (易支付 - Yipay)**: 处理实际的支付操作。
*   **数据库 (MongoDB Atlas)**: 存储订单信息、激活码信息等。
*   **邮件服务**: 用于发送包含激活码的邮件给用户。

## 3. 详细流程步骤

### 3.1 用户发起购买 (前端 -> 后端 `api/create-order.js`)

1.  **用户操作**:
    *   在前端网站选择需要购买的产品套餐（例如：WZS_PRO_PERPETUAL）。
    *   填写邮箱地址 (`email`)。
    *   选择支付方式 (`paymentType`，例如：alipay)。
    *   点击购买按钮。

2.  **前端请求**:
    *   前端将收集到的信息（产品ID、金额、支付方式、邮箱）通过 POST 请求发送到后端 API `/api/create-order` (部署于阿里云ECS)。

3.  **后端处理 (`api/create-order.js` - 运行于阿里云ECS)**:
    *   **CORS 处理**: 响应 OPTIONS 预检请求，允许跨域访问。
    *   **参数校验**:
        *   校验请求体中是否包含必要的参数（`email`, `productId`, `amount`, `paymentType`）。
        *   校验 `email` 格式是否正确。
    *   **生成内部订单号**:
        *   生成一个全局唯一的订单号 (`orderNo`)，例如 `WZS` + 时间戳 + 随机数。
    *   **准备支付网关参数**:
        *   `pid`: 支付商户ID (从环境变量 `PAYMENT_YIPAY_PID` 读取)。
        *   `type`: 支付类型 (从请求参数 `paymentType` 获取)。
        *   `out_trade_no`: 商户订单号 (使用生成的 `orderNo`)。
        *   `notify_url`: 异步回调地址 (例如 `https://<您的阿里云ECS域名>/api/payment-callback`)。
        *   `return_url`: 同步跳转地址 (例如 `https://<您的前端域名或GitHub Pages域名>/purchase-success.html`)。
        *   `name`: 商品名称 (从请求参数 `description` 或根据 `productId` 生成)。
        *   `money`: 支付金额 (从请求参数 `amount` 获取，并格式化为两位小数的字符串)。
        *   `sign_type`: 签名类型，固定为 `MD5`。
    *   **计算签名**:
        *   将上述参数（除`sign`和`sign_type`外）按字母顺序排序。
        *   拼接成 `key=value&key=value...` 的形式。
        *   在末尾追加 MD5 密钥 (从环境变量 `PAYMENT_YIPAY_MD5_KEY` 读取)。
        *   计算 MD5 哈希值作为签名 (`sign`)。
    *   **数据库操作 (MongoDB)**:
        *   检查 `MONGODB_URI` 环境变量是否设置。
        *   连接到 MongoDB。
        *   使用 `DB_NAME` 环境变量（默认为 `wenzisou`）指定的数据库。
        *   在 `orders` 集合中插入一条新的订单记录，包含以下主要字段：
            *   `orderNo`: 内部订单号。
            *   `userEmail`: 用户邮箱。
            *   `productId`: 产品ID。
            *   `amount`: 订单金额 (数值类型)。
            *   `paymentType`: 支付方式。
            *   `status`: 订单状态，初始为 `pending`。
            *   `createdAt`: 订单创建时间。
            *   `paymentGatewayParams`: (可选) 存储发送给支付网关的参数。
        *   记录日志，确认订单已存入数据库。
        *   关闭 MongoDB 连接。
    *   **构建支付网关 URL**:
        *   将包含签名的所有参数构造成支付网关的请求 URL (例如 `https://pay.myzfw.com/submit.php?...`)。
    *   **响应前端**:
        *   返回状态码 `200 OK`。
        *   在响应体中返回包含支付网关 URL 的 JSON 对象，例如 `{ paymentUrl: "..." }`。

4.  **前端跳转**:
    *   前端收到响应后，将用户重定向到返回的 `paymentUrl`，用户在支付网关完成支付。

### 3.2 支付网关处理与回调 (支付网关 -> 后端 `api/payment-callback.js`)

1.  **用户支付**: 用户在支付网关页面完成支付操作。
2.  **支付网关异步通知**:
    *   支付成功后，支付网关会向 `api/create-order.js` 中指定的 `notify_url` (`https://<您的阿里云ECS域名>/api/payment-callback`) 发送一个 GET 请求 (或 POST，具体取决于支付网关配置)。
    *   请求参数通常包含：
        *   `pid`: 商户ID。
        *   `trade_no`: 支付网关的交易流水号。
        *   `out_trade_no`: 商户订单号 (即之前生成的 `orderNo`)。
        *   `type`: 支付类型。
        *   `name`: 商品名称。
        *   `money`: 支付金额。
        *   `trade_status`: 交易状态 (例如 `TRADE_SUCCESS`)。
        *   `sign`: 支付网关生成的签名。
        *   `sign_type`: 签名类型。

3.  **后端处理 (`api/payment-callback.js`)**:
    *   **记录回调接收**: 记录接收到回调请求的日志，包括请求方法和所有参数。
    *   **参数提取**: 从请求查询参数中提取所有必要信息。
    *   **签名验证**:
        *   获取支付网关 MD5 密钥 (从环境变量 `PAYMENT_YIPAY_MD5_KEY` 读取)。
        *   将接收到的参数（除`sign`和`sign_type`外，以及空值参数）按字母顺序排序。
        *   拼接成 `key=value&key=value...` 的形式。
        *   在末尾追加 MD5 密钥。
        *   计算 MD5 哈希值。
        *   与接收到的 `sign` 参数进行比较。
        *   如果签名不匹配，记录错误日志并响应支付网关 `fail` (或其他约定失败字符串)，终止后续处理。
        *   如果签名匹配，记录成功日志。
    *   **交易状态检查**:
        *   检查回调参数中的 `trade_status` 是否为 `TRADE_SUCCESS` (或其他表示成功的状态)。
        *   如果交易状态不是成功，记录日志并响应 `fail`，终止后续处理。
        *   如果交易状态成功，记录成功日志。
    *   **数据库操作 (MongoDB)**:
        *   检查 `MONGODB_URI` 环境变量是否设置。
        *   连接到 MongoDB。
        *   使用 `DB_NAME` 环境变量（默认为 `wenzisou`）指定的数据库。
        *   在 `orders` 集合中根据 `out_trade_no` (即 `orderNo`) 查询订单。
        *   **订单存在性检查**:
            *   如果未找到订单，记录错误日志（严重问题，可能意味着订单创建失败或回调参数错误），但为了防止支付网关重试，仍响应 `success`。
        *   **订单状态检查 (防止重复处理)**:
            *   如果找到订单，检查其 `status` 字段。
            *   如果订单状态已经是 `paid` (或其他表示已处理完成的状态)，记录日志（表示重复回调），响应 `success`。
        *   **金额校验 (可选但推荐)**:
            *   比较数据库中存储的订单金额 (`order.amount`) 与回调参数中的支付金额 (`money`)。
            *   如果金额不匹配，记录错误日志（严重安全问题），响应 `success` (防止重试，但需要人工介入)。
        *   **更新订单状态**:
            *   如果以上检查均通过，将订单的 `status` 更新为 `paid`。
            *   同时可以更新 `paidAt` (支付时间) 和 `paymentGatewayTradeNo` (支付网关流水号) 等字段。
            *   使用原子操作（如 `findOneAndUpdate`）确保并发安全。
            *   记录订单更新成功的日志。
    *   **生成激活码 (调用 `generateLicense` 函数)**:
        *   **输入**: `userEmail`, `productId` (从查询到的订单记录中获取)。
        *   **逻辑**:
            *   根据 `productId` 确定激活码的类型、有效期等规则。
            *   生成一个唯一的、不易猜测的激活码字符串 (例如，使用 UUID 结合特定前缀，或自定义算法，可结合 `LICENSE_SECRET` 环境变量增加复杂度)。
            *   可以考虑将激活码与用户信息（如邮箱部分哈希）和产品信息关联，增加校验。
        *   **输出**: 生成的激活码字符串 (`licenseKey`)。
        *   **存储激活码 (更新数据库)**:
            *   将生成的 `licenseKey` 和 `licenseGeneratedAt` (激活码生成时间) 更新到对应的订单文档中。
        *   **发送激活邮件 (调用 `sendLicenseEmail` 函数)**:
            *   **输入**: `userEmail`, `licenseKey`, `orderNo`。
            *   **邮件服务配置**: 从环境变量读取QQ邮箱的邮件服务器地址 (`EMAIL_SMTP_HOST`)、端口 (`EMAIL_SMTP_PORT`)、用户名 (`EMAIL_SMTP_USER`)、**授权码** (`EMAIL_SMTP_PASS`) 等。
            *   **邮件内容**: 构造包含激活码、产品名称、订单号、激活说明等的邮件正文。
            *   **发送**: 使用 `nodemailer` 或类似库发送邮件。
            *   **错误处理**: 记录邮件发送成功或失败的日志。即使邮件发送失败，也应认为支付回调处理成功，邮件问题后续可人工补发。
        *   **响应支付网关**:
            *   如果所有核心步骤（签名验证、状态检查、订单更新）成功，向支付网关响应 `success` (或其他约定成功字符串)。这很重要，否则支付网关可能会持续重试发送回调。
        *   **关闭数据库连接**: 在 `finally` 块中确保 MongoDB 连接被关闭。

### 3.3 用户同步跳转 (支付网关 -> 前端)

1.  用户在支付网关完成支付后，除了异步回调，支付网关通常还会将用户浏览器重定向到 `api/create-order.js` 中指定的 `return_url` (例如 `https://<您的前端域名或GitHub Pages域名>/purchase-success.html`)。
2.  `purchase-success.html` 页面可以向用户显示支付成功的信息，并提示用户检查邮箱以获取激活码。
3.  **注意**: `return_url` 的跳转不应作为支付成功的唯一凭证，因为这可能被伪造。业务逻辑的触发必须依赖于安全的、经过签名验证的异步 `notify_url` 回调。

### 3.4 激活码使用 (在线激活 - 桌面应用 -> 后端 `api/activate-license.js`)

*   用户收到包含激活码的邮件。
*   在文智搜产品的"许可证管理"激活界面输入激活码。
*   桌面产品客户端将激活码和设备唯一标识 (`deviceId`) 发送到后端 API (`https://<您的阿里云ECS域名>/api/activate-license`) 进行验证。
*   **后端 API (`api/activate-license.js` - 运行于阿里云ECS) 逻辑 (更新后)**:
    1.  **接收请求**: API 接收包含 `licenseKey` 和 `deviceId` (客户端生成的设备唯一标识) 的 POST 请求。
    2.  **参数校验**: 检查 `licenseKey` 和 `deviceId` 是否存在且格式基本正确。
    3.  **数据库查询**: 连接 MongoDB Atlas (使用 `MONGODB_URI` 和 `DB_NAME` 环境变量)，在 `orders` 集合中根据 `licenseKey` 查找订单。增加对 `MONGODB_URI` 未配置情况的错误处理和日志记录。
    4.  **验证激活码 (核心逻辑更新)**:
        *   **未找到激活码**: 如果在 `orders` 集合中找不到对应的 `licenseKey`，则返回"激活码无效"错误。
        *   **订单状态**: 检查 `order.status` 是否为 `"paid"`。如果不是，则返回"订单未支付"或类似错误。
        *   **是否已激活 (设备绑定)**:
            *   如果 `order.licenseDeviceId` 为空 (表示此付费订单的激活码从未被激活过):
                *   将当前请求的 `deviceId` 存入 `order.licenseDeviceId`。
                *   将当前服务器时间 (`new Date()`) 存入 `order.licenseActivatedAt`。
                *   (可选) 更新 `order.licenseStatus` 为 `"active"` (或其他表示已激活的状态)。
                *   数据库更新成功后，视为首次激活成功，构造成功响应，包含 `alreadyActivated: false`。
            *   如果 `order.licenseDeviceId` 已存在:
                *   若 `order.licenseDeviceId` 与请求中的 `deviceId` **相同**: 表示是同一设备在之前成功激活后再次请求（例如，应用重装后的状态检查或续期验证）。视为有效，构造成功响应，包含 `alreadyActivated: true` 和原始的 `licenseActivatedAt`。
                *   若 `order.licenseDeviceId` 与请求中的 `deviceId` **不同**: 表示该激活码已绑定到其他设备。返回"激活码已在其他设备使用"的错误。
        *   (可选) **产品有效期**: 对于非永久有效的产品，还需检查 `order.paidAt` (或 `order.licenseActivatedAt`) 加上产品有效期是否已超过当前时间。
    5.  **响应客户端 (更新后)**:
        *   **成功 (新激活)**: `res.status(200).json({ success: true, message: "激活成功！", userEmail: order.userEmail, productId: order.productId, activationDate: newActivationDateISOString, purchaseDate: order.paidAtISOString, alreadyActivated: false })` (日期应为ISO格式字符串)
        *   **成功 (已在同设备激活)**: `res.status(200).json({ success: true, message: "许可证状态有效。", userEmail: order.userEmail, productId: order.productId, activationDate: order.licenseActivatedAtISOString, purchaseDate: order.paidAtISOString, alreadyActivated: true })`
        *   **失败**: `res.status(400).json({ success: false, message: "激活失败：[具体原因，如：无效的激活码、订单未支付、激活码已在其他设备使用等]" })`。
    6.  **日志记录**: 在数据库连接、查询、验证的各个关键步骤记录详细日志。

*   **桌面客户端处理 (更新后)**:
    1.  **发送请求**: 用户点击"激活"后，客户端生成 `deviceId`，连同用户输入的 `licenseKey` 发送给后端API。
    2.  **处理响应**: 
        *   **成功**: 客户端接收到成功响应后，解析返回的JSON数据，包括 `userEmail`, `productId`, `activationDate`, `purchaseDate`, `alreadyActivated` 等。
        *   **本地存储**: 将这些信息（尤其是 `licenseKey`, `deviceId`, 激活状态, `activationDate`, `purchaseDate`, `userEmail`, `productId`)安全地加密存储在本地 (如注册表或配置文件)。
        *   **UI反馈**: 提示用户"激活成功"，更新许可证信息显示，并解锁相应功能。激活过程的用户体验得到优化，包括"请稍候"提示的正确管理以及激活对话框在操作后的响应性得到保证。
        *   **失败**: 提示用户具体的激活失败原因 (来自服务器的 `message`)。允许用户重试或联系支持。 `LicenseDialog` 的UI应保持可交互状态。

## 4. 关键数据结构 (MongoDB `orders` 集合示例)

```json
{
  "_id": ObjectId("..."),
  "orderNo": "WZS17469270434947318", // 内部订单号，唯一索引
  "userEmail": "563625618@qq.com",   // 用户邮箱，可加索引
  "productId": "WZS_PRO_PERPETUAL",  // 产品ID
  "amount": 1.00,                    // 订单金额 (Number)
  "paymentType": "alipay",           // 支付方式
  "status": "paid",                  // 订单状态: pending, paid, failed, refunded, expired
  "createdAt": ISODate("2025-05-11T01:30:43.492Z"), // 订单创建时间
  "paidAt": ISODate("2025-05-11T01:39:27.523Z"),   // 支付确认时间 (回调处理时更新)
  "paymentGatewayTradeNo": "2025051109310342747", // 支付网关交易号 (回调处理时更新)
  "licenseKey": "WZS-XXXX-YYYY-ZZZZ-AAAA", // 生成的激活码 (回调处理时更新)
  "licenseGeneratedAt": ISODate("..."), // 激活码生成时间
  "licenseSentAt": ISODate("..."),      // 激活码邮件发送时间 (可选)
  "licenseActivatedAt": ISODate("..."), // 激活时间 (通过 api/activate-license.js 更新)
  "licenseDeviceId": "unique-device-identifier-string", // 绑定的设备ID (通过 api/activate-license.js 更新)
  "licenseStatus": "active",            // 激活码状态 (e.g., pending, active, revoked, expired)
  "emailSendStatus": "success",         // 邮件发送状态 (可选: pending, success, failed)
  "notes": "Some notes about the order" // (可选) 备注
}
```

**说明 (针对`orders`集合示例的更新)**:
*   `licenseStatus`: 在订单创建并支付后，此字段可能为 `paid`。当激活码被成功激活后，可以考虑将此字段更新为 `active`，或者引入一个新的特定于许可证激活状态的字段。在上述激活逻辑中，我们侧重于检查 `status: "paid"` (订单支付状态)，并通过 `licenseDeviceId` 和 `licenseActivatedAt` 来管理激活状态。
*   `licenseDeviceId`: 初始化为 `null`，在首次成功激活时被填充。
*   `licenseActivatedAt`: 初始化为 `null`，在首次成功激活时被填充。
*   `paidAt`: 这个时间戳可以作为用户的"购买日期" (`purchaseDate`) 在API响应中返回给客户端。

## 5. 环境变量

确保以下环境变量在阿里云ECS服务器上正确配置：

*   `MONGODB_URI`: MongoDB 连接字符串 (包含认证信息)。
*   `DB_NAME`: MongoDB 数据库名称 (例如 `wenzisou`)。
*   `PAYMENT_YIPAY_PID`: 易支付商户ID。
*   `PAYMENT_YIPAY_MD5_KEY`: 易支付 MD5 密钥。
*   `YIPAY_API_URL`: 易支付接口基础 URL (例如 `https://pay.myzfw.com`)。
*   `LICENSE_SECRET`: 用于增强激活码生成或校验逻辑的强随机密钥 (可选，但推荐)。
*   `NODE_ENV`: 运行环境 (例如 `production` 或 `development`)。
*   `EMAIL_SMTP_HOST`: QQ邮箱邮件服务器地址 (例如 `smtp.qq.com`)。
*   `EMAIL_SMTP_PORT`: QQ邮箱邮件服务器端口 (例如 `465` for SSL, `587` for TLS)。
*   `EMAIL_SMTP_SECURE`: 是否为QQ邮箱使用 SSL/TLS (例如 `true` for port 465, `false` for port 587 with STARTTLS)。
*   `EMAIL_SMTP_USER`: QQ邮箱邮件服务器用户名 (您的QQ邮箱地址)。
*   `EMAIL_SMTP_PASS`: QQ邮箱邮件服务器**授权码**。
*   `EMAIL_FROM_ADDRESS`: 发件人邮箱地址 (通常与 `EMAIL_SMTP_USER` 一致)。
*   `EMAIL_FROM_NAME`: 发件人名称 (例如 "文智搜官方")。
*   `NOTIFY_URL_BASE`: 后端API服务的基础URL，用于构建回调地址 (例如 `https://<您的阿里云ECS域名>`)。
*   `FRONTEND_SUCCESS_URL`: 前端支付成功后同步跳转的完整URL (例如 `https://<您的前端域名或GitHub Pages域名>/purchase-success.html`)。

## 6. 日志与监控

*   在所有关键步骤（API 调用、数据库操作、支付交互、邮件发送）添加详细的日志记录。
*   使用 PM2 等工具管理 Node.js 应用，并配置日志轮转。
*   定期检查 `error.log` 和 `out.log`，监控系统运行状态。
*   **后端API日志**: 
    *   记录每个API请求的入口、关键参数、处理步骤（如数据库查询、外部API调用）、以及最终响应（包括错误响应）。
    *   `api/activate-license.js` 增加了更详细的日志，包括数据库连接尝试、激活验证步骤和结果。
    *   使用 `pm2` 等工具管理Node.js应用时，其日志功能（如 `pm2 logs`）可用于实时查看和管理日志文件。

## 7. 安全注意事项

*   **密钥安全**: `PAYMENT_YIPAY_MD5_KEY` 和 `EMAIL_SMTP_PASS` 等敏感信息必须通过环境变量配置，严禁硬编码到代码中。
*   **签名验证**: 严格执行支付回调的签名验证，防止伪造请求。
*   **参数校验**: 对所有外部输入（请求参数、回调参数）进行严格校验。
*   **防止重复处理**: 在支付回调中检查订单状态，避免同一订单被多次处理。
*   **金额校验**: 校验回调金额与订单金额是否一致，防止支付金额被篡改。
*   **HTTPS**: 所有涉及敏感数据的通信（前端到后端，后端到支付网关）都应使用 HTTPS。
*   **数据库安全**: MongoDB 访问应配置强密码，并限制访问IP（如果适用）。

## 8. 后续可扩展功能

*   退款处理流程。
*   优惠券/折扣码功能。
*   多产品、多套餐管理。
*   用户账户系统集成。
*   详细的销售统计和报表。
*   激活码管理后台（查询、吊销、重新发送等）。

---

此文档将随着功能的迭代而更新。
最后更新时间: 2025年5月12日 (阿里云ECS和在线激活流程更新) 