# app/common/logger.py
# 全局日志配置模块 —— 统一管理项目的日志输出格式和级别

import logging
import sys


# ==================== 日志格式 ====================
# 定义日志输出格式：时间 - 级别 - 模块名 - 消息内容
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


# ==================== 日志初始化函数 ====================
def setup_logging():
    """
    初始化全局日志配置
    在应用启动时调用一次，后续所有模块通过 getLogger 获取的 logger 都沿用此配置
    """
    logging.basicConfig(
        level=logging.INFO,                                # 日志级别：INFO 及以上（WARNING、ERROR、CRITICAL）会被输出
        format=LOG_FORMAT,                                 # 日志格式
        handlers=[
            logging.StreamHandler(sys.stdout),             # 输出到控制台（标准输出）
            logging.FileHandler("app.log"),                # 同时写入 app.log 文件，方便排查历史问题
        ]
    )


# ==================== 全局 Logger 实例 ====================
# 创建一个名为 "AI_Chef" 的 logger，其他模块可通过此名称获取同一个实例
logger = logging.getLogger("AI_Chef")