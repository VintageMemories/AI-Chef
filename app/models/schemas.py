# app/models/schemas.py
# 数据模型定义
"""
【本文件职责】
使用 Pydantic 定义项目中用到的数据模型（请求体、响应体等）。
Pydantic 会自动完成数据校验、类型转换、JSON Schema 生成等功能。

【与其他模块的关系】
- ChatRequest 被 app.api.v1.chat 引用，用于 FastAPI 的请求体验证
- FastAPI 会根据 ChatRequest 自动生成 API 文档（Swagger UI）中的请求体描述
"""

from typing import Optional
from pydantic import BaseModel


# ==================== 聊天请求体 ====================
class ChatRequest(BaseModel):
    """
    聊天请求数据模型。

    【字段说明】
    - message:   必填，用户输入的文本消息
    - image_url: 可选，用户上传的食材图片 URL（经过 OSS 上传后得到的地址）
    - thread_id: 必填，对话线程标识符，用于关联同一个用户的连续对话

    【数据校验规则（Pydantic 自动执行）】
    - message 必须是字符串类型
    - image_url 可以是字符串或 None（None 表示纯文本对话）
    - thread_id 必须是字符串类型
    - 如果前端传了多余字段，会被自动忽略
    """
    message: str                                            # 用户消息文本（必填）
    image_url: Optional[str] = None                         # 图片链接（可选，默认为 None）
    thread_id: str                                          # 对话线程 ID（必填，用于区分不同会话）