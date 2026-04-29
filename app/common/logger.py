# app/common/logger.py
# 全局日志配置模块 —— 统一管理项目的日志输出格式和级别
"""
【本文件职责】
封装 Python 标准库 logging，为整个项目提供统一的日志输出能力。

【与其他模块的关系】
- setup_logging() 在 app/main.py 启动时最早调用，全局生效
- logger 实例被 app/agents/ai_chef.py 直接导入使用，记录 Agent 运行日志
- 也可以被项目中任何其他模块通过 logging.getLogger("AI_Chef") 获取同一实例

【输出目标】
- 控制台（stdout）：开发时实时查看
- app.log 文件：持久化保存，方便排查历史问题
"""

import logging
import sys


# ==================== 日志格式 ====================
# 定义日志输出格式：时间 - 级别 - 模块名 - 消息内容
# 示例输出：2026-04-30 10:30:45,123 - INFO - AI_Chef - [用户]: 我有鸡蛋和番茄...
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


# ==================== 日志初始化函数 ====================
def setup_logging():
    """
    初始化全局日志配置。

    【调用时机】
    在 app/main.py 中，FastAPI 应用实例创建之前调用。
    调用一次后，全局 logging 模块的配置即生效，
    后续所有通过 getLogger 获取的 logger 都沿用此配置。

    【配置内容】
    - level=INFO：只记录 INFO 及以上级别（WARNING、ERROR、CRITICAL）
    - format：按 LOG_FORMAT 格式输出
    - handlers：同时输出到控制台和文件（双通道）
    """
    logging.basicConfig(
        level=logging.INFO,                                # 日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
        format=LOG_FORMAT,                                 # 日志格式模板
        handlers=[
            logging.StreamHandler(sys.stdout),             # 输出到控制台（标准输出流）
            logging.FileHandler("app.log"),                # 同时写入 app.log 文件（追加模式）
        ]
    )


# ==================== 全局 Logger 实例 ====================
# 创建一个名为 "AI_Chef" 的 logger 实例
# 其他模块（如 ai_chef.py）通过 `from app.common.logger import logger` 直接使用
# 也可以在其他模块中通过 `logging.getLogger("AI_Chef")` 获取同一个实例
#
# 注意：如果其他模块在 setup_logging() 之前获取了 logger，日志配置可能未生效，
# 因此 app/main.py 中 setup_logging() 的调用必须在所有 import 之前（或尽早执行）
logger = logging.getLogger("AI_Chef")