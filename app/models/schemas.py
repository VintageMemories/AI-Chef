# app/models/schemas.py
# 数据模型定义

from typing import Optional
from pydantic import BaseModel


# ==================== 聊天请求体 ====================
class ChatRequest(BaseModel):
    """聊天请求数据模型"""
    message: str                      # 用户输入的消息文本
    image_url: Optional[str] = None   # 可选的图片 URL（用于上传食材照片）
    thread_id: str                    # 对话线程 ID，用于区分不同会话