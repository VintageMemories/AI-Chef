from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
import os  # Python 标准库，用于读取操作系统环境变量

# 加载 .env 文件中的环境变量
from dotenv import load_dotenv
load_dotenv()  # 执行后，.env 中的键值对会被注入到 os.environ 中，可通过 os.getenv() 读取

# ==================== 模型初始化 ====================
# 初始化阿里云百炼平台的千问（Qwen）大语言模型
model = init_chat_model(
    model="qwen3.6-plus",  # 指定具体模型：千问 3.6 Plus 版本（阿里云百炼平台模型 Code）
    model_provider="openai",  # API 协议格式：OpenAI 兼容模式（非服务商，LangChain 内部按 OpenAI 格式组装请求）
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云 DashScope 兼容 OpenAI 的 API 端点
    api_key=os.getenv("DASHSCOPE_API_KEY"),  # 从环境变量读取阿里云百炼平台的 API Key
)

# ==================== 工具创建 ====================
# 创建 Tavily 搜索工具实例，为 Agent 提供联网搜索能力
tavily_search = TavilySearch(
    max_results=5,    # 每次搜索返回的最大结果数，设为 5 以平衡信息获取量和响应速度
    topic="general",  # 搜索主题类型："general" 表示通用搜索，"news" 则为新闻搜索
)

# ==================== 系统提示词定义 ====================
# 定义 Agent 的角色身份、执行流程、工具使用规则和输出格式要求
system_prompt = """
你是一名私人厨师。你的任务是：根据用户提供的食材照片或清单，推荐营养丰富且制作简单的菜谱。

【执行流程】
1. 识别食材：若用户提供照片，列出所有可见食材及新鲜度评估。
2. 搜索菜谱：调用 tavily_search 工具搜索可行菜谱。
3. 评估排序：从营养价值和制作难度两个维度打分，简单且营养高的排前面。
4. 输出报告：结构化输出，包含菜谱、得分、推荐理由、参考图片。

【工具调用规则】
- 唯一可用工具：tavily_search
- 必填参数：query（字符串，搜索关键词，如"西红柿鸡蛋做法"）
- 可选参数：search_depth（"basic" 为普通搜索，"advanced" 为深度搜索）、include_images（true 或 false，是否返回图片）
- 禁止传入其他任何多余参数，避免调用失败
- 必须基于搜索结果推荐菜谱，若搜索失败则如实告知用户，不要编造内容
"""

# ==================== 智能体创建 ====================
# 使用 create_agent 将模型、工具和系统提示词组装成一个可运行的智能体
# Agent 会自动根据用户输入决定何时调用工具、如何解析工具返回结果、如何组织最终回复
agent = create_agent(
    model=model,
    tools=[tavily_search],  # 可用工具列表
    system_prompt=system_prompt,
)
