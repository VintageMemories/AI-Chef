# app/api/v1/oss.py
# OSS 文件上传接口模块 —— 提供图片等文件的上传预签名 URL

import alibabacloud_oss_v2 as oss                                  # 阿里云 OSS Python SDK
from fastapi import APIRouter                                     # FastAPI 路由
from datetime import timedelta                                     # 用于设置签名过期时间
import os                                                         # 读取环境变量


# ==================== 创建路由 ====================
router = APIRouter()


# ==================== OSS 客户端初始化 ====================

# 从环境变量中加载凭证信息（AccessKey ID 和 AccessKey Secret）用于身份验证
credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()

# 加载 SDK 的默认配置，并设置凭证提供者
config = oss.config.load_default()
config.credentials_provider = credentials_provider

# 指定 OSS 所在的 Region（地域），SDK 会根据 Region 自动构造 HTTPS 访问域名
config.region = 'cn-beijing'

# 使用配置好的信息创建 OSS 客户端实例
client = oss.Client(config)

# OSS 域名配置 —— 优先从环境变量读取，默认为北京地域的公网域名
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")

# OSS 存储桶名称 —— 从环境变量读取
OSS_BUCKET = os.getenv("OSS_BUCKET")


# ==================== 1. 获取上传预签名 URL ====================
@router.get("/oss/presign")
def chat_endpoint(filename: str):
    """
    生成 OSS 预签名上传 URL（GET 请求）
    前端获取此 URL 后可直传文件到 OSS，无需经过后端服务器中转

    参数:
        filename: 要上传的文件名，通过查询参数传入，例如 /oss/presign?filename=photo.jpg

    返回:
        uploadUrl:   预签名上传地址（前端用此地址 PUT 文件）
        contentType: 文件的 MIME 类型
        accessUrl:   上传成功后文件的公开访问地址
    """

    # ---- 根据文件扩展名确定 MIME 类型 ----
    content_type_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    # 提取文件扩展名并转为小写，没有扩展名则默认按 jpg 处理
    ext = filename.split(".")[-1].lower() if "." in filename else "jpg"
    content_type = content_type_map.get(ext, "application/octet-stream")

    # ---- 生成预签名 PUT 请求 ----
    pre_result = client.presign(oss.PutObjectRequest(
        bucket=OSS_BUCKET,                 # 目标存储桶
        key=filename,                      # 上传后的文件名（OSS 中的 object key）
        content_type=content_type,         # 文件 MIME 类型
        expires=3600                       # 签名有效期：1 小时
    ))

    # ---- 返回给前端 ----
    return {
        "uploadUrl": pre_result.url.strip('"'),                              # 预签名 URL（去掉两端引号）
        "contentType": content_type,                                         # MIME 类型
        "accessUrl": f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{filename}"       # 上传成功后的公开访问路径
    }