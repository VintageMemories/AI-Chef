# app/agents/ai_chef.py
# AI 厨师 Agent —— 根据食材推荐菜谱的智能助手

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
model = init_chat_model(
    model="qwen3.6-plus",
    model_provider="openai",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),                # 从环境变量读取阿里云百炼平台的 API Key
)


# ==================== 工具创建 ====================
# 创建 Tavily 搜索工具实例，为 Agent 提供联网搜索能力
tavily_search = TavilySearch(
    max_results=5,                                         # 每次搜索返回的最大结果数
    topic="general",                                       # 搜索主题类型："general" 表示通用搜索，"news" 则为新闻搜索
)

connection = sqlite3.connect("app/db/ai_chef.db", check_same_thread=False)
# 初始化checkpointer
checkpointer = SqliteSaver(connection)
# 自动建表
checkpointer.setup()

# ==================== 系统提示词定义 ====================
# 定义 Agent 的角色身份、执行流程、工具使用规则和输出格式要求
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
# 使用 create_agent 将模型、工具和系统提示词组装成一个可运行的智能体
# Agent 会自动根据用户输入决定何时调用工具、如何解析工具返回结果、如何组织最终回复
agent = create_agent(
    model=model,
    tools=[tavily_search],
    checkpointer=checkpointer,
    system_prompt=system_prompt,
)

# 流式对话
async def search_recipes(prompt: str, image: str, thread_id: str):
    """调用agent搜索食谱"""
    logger.info(f"[用户]: {prompt}, image: {image}, thread_id: {thread_id}")
    try:
        # 判断是否有图片，封装不同格式的消息
        if not image or image.strip() == "":
            message = HumanMessage(content=prompt)
        else:
            message = HumanMessage(content=[
                {"type": "image", "url": image},
                {"type": "text", "text": prompt}
            ])

        # 流式调用Agent
        for chunk, metadata in agent.stream(
                {"messages": [message]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield chunk.content

    except Exception as e:
        logger.error(f"\n[错误]: {str(e)}")
        yield "信息检索失败，试试看手动输入食物列表？"

# 清空会话
def clear_messages(thread_id: str):
    """清空会话"""
    logger.info(f"清空历史消息，thread_id: {thread_id}")
    checkpointer.delete_thread(thread_id)

# 查询会话历史
def get_messages(thread_id: str) -> list[dict[str, str]]:
    """获取会话历史"""
    logger.info(f"获取历史消息，thread_id: {thread_id}")

    # 根据 thread_id 查询 checkpoint
    checkpoint = checkpointer.get({"configurable": {"thread_id": thread_id}})

    # 如果不存在，返回空列表
    if not checkpoint:
        return []

    # 安全获取 messages
    channel_values = checkpoint.get("channel_values")
    if not channel_values:
        return []

    messages = channel_values.get("messages", [])
    if not messages:
        return []

    # 转换消息格式
    result = []
    for msg in messages:
        if not msg.content:
            continue

        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            result.append({"role": "assistant", "content": msg.content})

    return result