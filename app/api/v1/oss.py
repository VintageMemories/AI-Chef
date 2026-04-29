# app/api/v1/oss.py
# OSS 文件上传接口模块 —— 提供图片等文件的上传预签名 URL
"""
【本文件职责】
为前端提供阿里云 OSS（对象存储服务）的预签名上传 URL。
前端拿到这个 URL 后，可以直接将文件上传到 OSS，无需经过后端服务器中转。

【为什么这样设计？】
- 图片文件可能很大（几 MB 到几十 MB），如果经过后端中转，会占用服务器带宽和内存
- 使用预签名 URL，文件从用户浏览器直传到 OSS，后端只负责生成签名授权
- 速度快、成本低、服务器压力小

【与其他模块的关系】
- 被 app/main.py 注册到 /api/v1 路由下
- 前端上传食材图片时，先调用 GET /api/v1/oss/presign?filename=xxx 获取上传地址
- 前端拿到 uploadUrl 后，直接 PUT 文件到 OSS
- 上传成功后，用 accessUrl 作为 image_url 参数调用聊天接口
"""

import alibabacloud_oss_v2 as oss                                  # 阿里云 OSS Python SDK v2
from fastapi import APIRouter                                     # FastAPI 路由
from datetime import timedelta                                     # 用于设置签名过期时间
import os                                                         # 读取环境变量


# ==================== 创建路由 ====================
router = APIRouter()


# ==================== OSS 客户端初始化 ====================
# 以下代码在模块加载时执行一次，创建全局单例 OSS 客户端

# 从环境变量中加载凭证信息（AccessKey ID 和 AccessKey Secret）用于身份验证
# EnvironmentVariableCredentialsProvider 会自动读取环境变量：
#   ALIBABA_CLOUD_ACCESS_KEY_ID
#   ALIBABA_CLOUD_ACCESS_KEY_SECRET
credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()

# 加载 SDK 的默认配置，并设置凭证提供者
config = oss.config.load_default()
config.credentials_provider = credentials_provider

# 指定 OSS 所在的 Region（地域），SDK 会根据 Region 自动构造 HTTPS 访问域名
# 例如 cn-beijing → https://oss-cn-beijing.aliyuncs.com
config.region = 'cn-beijing'

# 使用配置好的信息创建 OSS 客户端实例（全局复用，不每次新建）
client = oss.Client(config)

# OSS 域名配置 —— 优先从环境变量读取，默认为北京地域的公网域名
# 这个域名用于构造文件的公开访问 URL
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")

# OSS 存储桶名称 —— 从环境变量读取，必须在 .env 中配置
# Bucket 是 OSS 中存储对象的容器，类似文件系统中的"根目录"
OSS_BUCKET = os.getenv("OSS_BUCKET")


# ==================== 1. 获取上传预签名 URL ====================
@router.get("/oss/presign")
def chat_endpoint(filename: str):
    """
    生成 OSS 预签名上传 URL（GET 请求）。

    前端获取此 URL 后可直传文件到 OSS，无需经过后端服务器中转。

    【参数】
        filename: 要上传的文件名，通过查询参数传入
                  例如：GET /api/v1/oss/presign?filename=photo.jpg

    【返回】
        {
            "uploadUrl":   "https://bucket.oss-cn-beijing.aliyuncs.com/photo.jpg?signature=...",
            "contentType": "image/jpeg",
            "accessUrl":   "https://bucket.oss-cn-beijing.aliyuncs.com/photo.jpg"
        }

    【工作原理】
    1. SDK 使用 AccessKey 对上传请求进行签名，生成带签名的临时 URL
    2. 签名信息编码在 URL 的查询参数中（?Expires=...&OSSAccessKeyId=...&Signature=...）
    3. OSS 收到 PUT 请求时验证签名，通过后允许上传
    4. 签名有时效性（这里设为 1 小时），过期后 URL 失效，防止被滥用
    """

    # ---- 根据文件扩展名确定 MIME 类型 ----
    # MIME 类型告诉浏览器/OSS 这个文件的格式，影响下载时的处理方式
    content_type_map = {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif":  "image/gif",
        ".webp": "image/webp",
    }

    # 提取文件扩展名并转为小写
    # 例如 "photo.JPG" → ".jpg"，没有扩展名则默认按 jpg 处理
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = content_type_map.get(ext, "application/octet-stream")
    # application/octet-stream 是通用二进制流类型，用于未知文件格式

    # ---- 生成预签名 PUT 请求 ----
    # client.presign() 会：
    #   1. 构造一个标准的 PutObjectRequest
    #   2. 用 AccessKey 对其签名
    #   3. 返回包含签名的完整 URL
    pre_result = client.presign(oss.PutObjectRequest(
        bucket=OSS_BUCKET,                 # 目标存储桶名称
        key=filename,                      # 上传后的文件名（OSS 中的 object key）
        content_type=content_type,         # 文件 MIME 类型（上传时声明）
        expires=3600                       # 签名有效期：3600 秒 = 1 小时
    ))

    # ---- 返回给前端 ----
    return {
        # 预签名上传 URL：前端用此地址发送 PUT 请求上传文件
        # SDK 返回的 URL 可能带引号，用 strip('"') 去掉
        "uploadUrl": pre_result.url.strip('"'),

        # MIME 类型：前端上传时需要在请求头中设置 Content-Type
        "contentType": content_type,

        # 上传成功后的公开访问路径：用于后续聊天接口的 image_url 参数
        # 格式：https://<bucket>.<endpoint>/<filename>
        "accessUrl": f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{filename}"
    }