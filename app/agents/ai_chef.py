# app/agents/ai_chef.py
# AI 厨师 Agent —— 根据食材推荐菜谱的智能助手
"""
【本文件职责】
这是整个项目的"大脑"——AI 厨师 Agent。
它利用 LangChain/LangGraph 框架，将大模型 + 搜索工具 + 提示词组合成一个智能体，
能够根据用户提供的食材（文字或图片）自动搜索菜谱、评估打分、生成结构化报告。

【运作流程】
1. 初始化混元大模型（通过阿里云百炼平台兼容的 OpenAI 接口调用）
2. 初始化 Tavily 联网搜索工具（用于搜索菜谱和图片）
3. 初始化 SQLite Checkpointer（用于持久化对话历史，让 Agent 拥有"记忆"）
4. 定义系统提示词（设定 Agent 的角色、行为规范和输出格式）
5. 使用 LangChain create_agent 将以上组件组装成 Agent
6. 对外暴露三个接口函数：search_recipes（流式对话）、get_messages（获取历史）、clear_messages（清空历史）
"""

from langchain.chat_models import init_chat_model          # LangChain 统一模型初始化接口
from langchain_core.messages import HumanMessage, AIMessageChunk, AIMessage
from langchain_core.tools import tool
from langchain_tavily import TavilySearch                  # Tavily 联网搜索工具
from langchain.agents import create_agent                  # LangChain 创建 Agent 的工厂函数
from app.common.logger import logger
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os                                                  # Python 标准库，用于读取操作系统环境变量

# 加载 .env 文件中的环境变量
from dotenv import load_dotenv
load_dotenv()                                              # 执行后，.env 中的键值对会被注入到 os.environ 中，可通过 os.getenv() 读取


# ==================== 模型初始化 ====================
# 初始化阿里云百炼平台的 Qwen3.6-Plus 模型
# init_chat_model 是 LangChain 的统一入口，通过 model_provider="openai" 使用 OpenAI 兼容协议对接
model = init_chat_model(
    model="qwen3.6-plus",                                   # 指定使用的模型名称
    model_provider="openai",                                # 使用 OpenAI 兼容接口协议
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云百炼平台 API 地址
    api_key=os.getenv("DASHSCOPE_API_KEY"),                # 从环境变量读取 API Key（存储在 .env 文件中）
)


# ==================== 工具创建 ====================
# 创建 Tavily 搜索工具实例，为 Agent 提供联网搜索能力
# Tavily 是一个专为 AI Agent 优化的搜索引擎，Agent 会自动调用它来获取菜谱信息
tavily_search = TavilySearch(
    max_results=5,                                         # 每次搜索返回的最大结果数（控制信息量，避免 token 爆炸）
    topic="general",                                       # 搜索主题类型："general" 表示通用搜索，"news" 则为新闻搜索
)

# ==================== 持久化机制 ====================
# 创建 SQLite 数据库连接，用于存储 LangGraph 的对话 checkpoint
# check_same_thread=False 是因为 FastAPI 的多线程环境下，同一个连接对象可能被不同线程使用
connection = sqlite3.connect("app/db/ai_chef.db", check_same_thread=False)

# 初始化 LangGraph 的 Checkpointer（检查点保存器）
# Checkpointer 的作用：将 Agent 的每一次推理状态（包括对话历史）持久化到 SQLite
# 这样即使是不同的请求，只要 thread_id 相同，Agent 就能"记住"之前的对话上下文
checkpointer = SqliteSaver(connection)

# 自动建表：如果数据库中还没有存储 checkpoint 所需的表，则自动创建
checkpointer.setup()


# ==================== 系统提示词定义 ====================
# 系统提示词是 Agent 的"角色说明书"，定义它的身份、行为规范、工具使用方式和输出格式
# 这个提示词会作为 SystemMessage 自动注入到每次 Agent 推理的上下文中
system_prompt = """
你是一名私人厨师。你的任务是：根据用户提供的食材照片或清单，推荐营养丰富且制作简单的菜谱。

【执行流程】
1. 识别食材：若用户提供照片，列出所有可见食材及新鲜度评估。
2. 搜索菜谱：为每个候选菜谱分别调用 tavily_search 工具搜索，确保获取足够的菜谱信息和图片。
3. 评估排序：从营养价值和制作难度两个维度打分，简单且营养高的排前面。
4. 输出报告：结构化输出，包含菜谱、得分、推荐理由、参考图片。

【工具调用规则】
- 唯一可用工具：tavily_search
- 必填参数：query（字符串，搜索关键词）
- 每次搜索必须设置 include_images=true
- 搜索关键词要具体，格式为"菜名 做法 图片"，例如"西红柿炒鸡蛋 做法 图片"
- 禁止传入其他任何多余参数，避免调用失败
- 必须基于搜索结果推荐菜谱，若搜索失败则如实告知用户，不要编造内容

【输出格式要求】
- 每个推荐菜谱必须尝试附上参考图片，格式为：![菜名](图片URL)
- 图片必须来自 tavily_search 返回结果中的真实图片链接
- 如果某个菜谱确实搜不到图片，写上"（暂无参考图片）"
- 严禁编造图片链接，严禁使用占位图
"""


# ==================== 智能体创建 ====================
# create_agent 是 LangChain 提供的工厂函数，它内部实际创建了一个 LangGraph 图结构
# 这个图由"LLM 节点"和"工具节点"组成，Agent 会自动在两者之间循环：
#   1. 用户消息进入 LLM 节点 → 模型判断是否需要调用工具
#   2. 如果需要，进入工具节点执行 tavily_search → 结果返回 LLM 节点
#   3. 如果不需要，模型直接生成最终回复 → 返回给用户
# Checkpointer 会在每一步后自动保存状态到 SQLite
agent = create_agent(
    model=model,                                            # 指定底层大模型
    tools=[tavily_search],                                  # 注册可用工具列表
    checkpointer=checkpointer,                              # 注入持久化器（实现记忆功能）
    system_prompt=system_prompt,                            # 注入系统提示词
)


# ==================== 流式对话函数 ====================
async def search_recipes(prompt: str, image: str, thread_id: str):
    """
    调用 Agent 进行流式菜谱搜索。
    这是整个 Agent 对外暴露的核心接口，被 FastAPI 路由层调用。

    【参数说明】
    - prompt: 用户输入的文本消息（如"我有西红柿和鸡蛋，可以做什么菜？"）
    - image:   用户上传的图片 URL（可选，为空时仅文本对话）
    - thread_id: 对话线程 ID，用于区分不同用户的会话，也是 Checkpointer 存取状态的 key

    【返回值】
    - 异步生成器（AsyncGenerator），逐块产出 Agent 回复的文本片段
    - FastAPI 的 StreamingResponse 会消费这个生成器，通过 SSE 推送给前端

    【工作流程】
    1. 根据是否有图片，构建 HumanMessage（纯文本或多模态）
    2. 调用 agent.stream() 进入 Agent 执行循环
    3. Agent 内部自动完成：理解用户意图 → 调用工具搜索 → 整理结果
    4. 每生成一个文本块（AIMessageChunk），立即 yield 出去
    5. 前端通过 EventSource 实时接收并逐字渲染
    """
    logger.info(f"[用户]: {prompt}, image: {image}, thread_id: {thread_id}")
    try:
        # ── 步骤1：构建用户消息 ──
        # LangChain 支持多模态消息：content 可以是纯文本字符串，也可以是字典列表
        if not image or image.strip() == "":
            # 纯文本消息
            message = HumanMessage(content=prompt)
        else:
            # 多模态消息：包含图片和文本
            # content 是一个列表，每个元素是一个字典，指定 type（text/image）
            message = HumanMessage(content=[
                {"type": "image", "url": image},            # 图片块：传入图片 URL
                {"type": "text", "text": prompt}            # 文本块：用户的文字输入
            ])

        # ── 步骤2：流式调用 Agent ──
        # agent.stream() 会启动 LangGraph 的执行图
        # 参数1 {"messages": [message]}：将用户消息放入消息列表
        # 参数2 {"configurable": {"thread_id": thread_id}}：指定会话 ID 以启用记忆
        # stream_mode="messages"：以消息粒度流式输出（逐 token）
        for chunk, metadata in agent.stream(
                {"messages": [message]},                     # 输入：包含用户消息的列表
                {"configurable": {"thread_id": thread_id}},  # 会话配置：绑定到特定 thread
                stream_mode="messages"                       # 流模式：逐消息块输出
        ):
            # ── 步骤3：过滤并输出有效内容块 ──
            # chunk 可能是 AIMessageChunk（有文本内容）或 ToolMessage（工具调用结果）
            # 我们只 yield 有实际文本内容的 AIMessageChunk，避免把工具内部调用细节暴露给用户
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content                         # yield 使这个函数成为异步生成器

    except Exception as e:
        # ── 异常处理 ──
        # 如果搜索失败（如网络问题、API 限额等），返回友好提示，不抛出异常导致接口崩溃
        logger.error(f"\n[错误]: {str(e)}")
        yield "信息检索失败，试试看手动输入食物列表？"


# ==================== 会话管理函数 ====================
def clear_messages(thread_id: str):
    """
    清空指定会话的全部对话历史。
    内部通过 Checkpointer 删除对应 thread_id 的所有 checkpoint。

    【使用场景】
    - 用户点击"开始新对话"按钮
    - 前端调用 DELETE /api/v1/chat/messages?thread_id=xxx
    """
    logger.info(f"清空历史消息，thread_id: {thread_id}")
    checkpointer.delete_thread(thread_id)                   # 删除该 thread 的所有持久化状态


def get_messages(thread_id: str) -> list[dict[str, str]]:
    """
    获取指定会话的完整对话历史。

    【参数】
    - thread_id: 会话 ID

    【返回】
    - 消息列表，每个元素为 {"role": "user"|"assistant", "content": "..."}

    【工作流程】
    1. 通过 Checkpointer 读取该 thread 的最新 checkpoint
    2. 从 checkpoint 的 channel_values 中提取 messages 列表
    3. 将 LangChain 消息对象转换为前端友好的 dict 格式
    """
    logger.info(f"获取历史消息，thread_id: {thread_id}")

    # 步骤1：根据 thread_id 查询 checkpoint
    checkpoint = checkpointer.get({"configurable": {"thread_id": thread_id}})

    # 步骤2：如果不存在，返回空列表（新会话还没有任何消息）
    if not checkpoint:
        return []

    # 步骤3：安全获取 channel_values（checkpoint 中的核心数据载体）
    channel_values = checkpoint.get("channel_values")
    if not channel_values:
        return []

    # 步骤4：从 channel_values 中提取 messages
    messages = channel_values.get("messages", [])
    if not messages:
        return []

    # 步骤5：格式转换 —— LangChain 消息对象 → 前端友好的 dict
    result = []
    for msg in messages:
        # 跳过空内容的消息
        if not msg.content:
            continue

        # 根据消息类型映射 role 字段
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})
        # 注意：ToolMessage 被过滤掉，前端不需要看到工具调用的内部细节

    return result