"""
【本文件职责】
聊天相关的 API 路由层，是前端和后端 AI Agent 之间的"接线员"。
它负责接收 HTTP 请求、参数校验、调用 Agent、并返回响应。

【与其他模块的关系】
- 依赖 app.agents.ai_chef 的三个函数：search_recipes / get_messages / clear_messages
- 依赖 app.models.schemas.ChatRequest：定义请求体的数据结构
- 被 app.main 注册到 FastAPI 应用的路由表中
"""

from fastapi import APIRouter
from app.models.schemas import ChatRequest
from fastapi.responses import StreamingResponse           # FastAPI 的流式响应类（基于 SSE）
from app.agents.ai_chef import search_recipes, get_messages, clear_messages

# 创建子路由实例，所有聊天接口都挂载在这个 router 下
router = APIRouter()


@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """
    【核心接口】流式聊天端点

    请求方式：POST /api/v1/chat/stream
    请求体：  ChatRequest { message, image_url?, thread_id }
    返回：    SSE 流式响应（text/event-stream）

    【工作原理】
    1. 接收前端发来的 ChatRequest（包含用户消息、可选图片URL、会话ID）
    2. 调用 search_recipes() 获取异步生成器
    3. 将生成器包装为 StreamingResponse，设置 MIME 类型为 "text/event-stream"
    4. 前端通过 EventSource API 逐块接收文本增量，实现打字机效果

    【为什么用流式响应？】
    大模型生成回复需要时间（通常几秒到十几秒），如果等全部生成完再返回，
    用户会对着白屏干等。流式响应让用户看到文字逐字出现，体验更流畅自然。
    """
    return StreamingResponse(
        # search_recipes 是一个异步生成器，每次 yield 一个文本块
        search_recipes(request.message, request.image_url, request.thread_id),
        media_type="text/event-stream"                     # 标识这是 SSE 流
    )


@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """
    获取指定会话的历史消息列表。

    请求方式：GET /api/v1/chat/messages?thread_id=xxx
    返回：    JSON { messages: [{role, content}, ...] }

    【使用场景】
    - 用户刷新页面后恢复之前的对话记录
    - 前端初始化时加载最近一次会话
    """
    messages = get_messages(thread_id)                     # 调用 Agent 层获取历史
    return {"messages": messages}                          # 包装为统一响应格式


@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """
    清空指定会话的全部对话历史。

    请求方式：DELETE /api/v1/chat/messages?thread_id=xxx
    返回：    JSON { success: true }

    【使用场景】
    - 用户点击"新对话"按钮，清空当前会话
    """
    clear_messages(thread_id)                              # 调用 Agent 层清空记忆
    return {"success": True}