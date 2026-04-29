# app/main.py
# 应用入口 —— FastAPI 应用初始化、路由注册、中间件配置、启动命令
"""
【本文件职责】
整个后端服务的"总控台"。
负责：创建 FastAPI 实例、注册所有子路由、配置 CORS/静态文件等中间件、提供服务启动指令。

【启动方式】
- 开发环境：python -m app.main  或  python app/main.py
- 生产环境：uvicorn app.main:app --host 0.0.0.0 --port 8001

【路由架构总览】
  /                        → 返回前端首页 index.html
  /static/*                → 静态文件服务（CSS/JS/图片等）
  /api/v1/chat/stream      → POST 流式聊天接口
  /api/v1/chat/messages    → GET  获取历史消息
  /api/v1/chat/messages    → DELETE 清空历史消息
  /api/v1/oss/...          → OSS 文件上传相关接口（另一个路由模块）
"""

from dotenv import load_dotenv
load_dotenv()                                              # 在所有导入之前加载 .env，确保后续 os.getenv() 能读到

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 导入路由模块（各功能模块的子路由）
from app.api.v1 import chat                                # 聊天接口路由（本项目的核心）
from app.api.v1 import oss                                 # OSS 文件上传接口路由（用于上传食材图片）

# 导入日志配置
from app.common.logger import setup_logging


# ==================== 日志初始化 ====================
# 在应用启动前初始化日志系统，全局统一日志格式和输出目标
setup_logging()


# ==================== FastAPI 应用实例 ====================
# 创建 FastAPI 应用，这些元信息会显示在自动生成的 Swagger/ReDoc API 文档中
app = FastAPI(
    title="Personal Chief API",                            # API 文档标题
    description="私厨——基于 AI 的智能菜谱推荐助手",          # API 文档描述
    version="0.1.0",                                       # 版本号
)


# ==================== CORS 跨域配置 ====================
# CORS（跨域资源共享）中间件：允许前端（可能部署在不同域名/端口）访问后端 API
# 例如：前端运行在 localhost:3000，后端运行在 localhost:8001，没有 CORS 则浏览器会拦截请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                                   # 允许所有来源域名（开发方便，生产应限制）
    allow_credentials=True,                                # 允许携带 Cookie 等凭证
    allow_methods=["*"],                                   # 允许所有 HTTP 方法
    allow_headers=["*"],                                   # 允许所有请求头
)


# ==================== 路由注册 ====================
# 将 chat 子路由挂载到 /api/v1 前缀下
# 最终完整路径示例：POST /api/v1/chat/stream
app.include_router(chat.router, prefix="/api/v1")

# 将 oss 子路由挂载到 /api/v1 前缀下（用于图片上传，不在本次提供的代码中）
# 最终完整路径示例：POST /api/v1/oss/upload
app.include_router(oss.router, prefix="/api/v1")


# ==================== 静态文件服务 ====================
# 将 app/static 目录挂载为静态文件服务
# 前端可通过 /static/xxx 直接访问该目录下的文件（如 /static/style.css）
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ==================== 前端页面入口 ====================
@app.get("/")
async def root():
    """
    根路径返回前端单页应用入口文件。
    用户访问 http://localhost:8001 时，直接看到前端界面。
    """
    return FileResponse("app/static/index.html")


# ==================== 启动入口 ====================
if __name__ == "__main__":
    import uvicorn
    # Python 脚本直接运行时（非 import），启动 Uvicorn 服务器
    # 等效于命令行：uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
    uvicorn.run(
        "app.main:app",                                    # 模块路径:应用实例名
        host="127.0.0.1",                                  # 监听本地，仅本机可访问
        port=8001,                                         # 监听 8001 端口
        reload=True                                        # 代码热重载：文件修改后自动重启（仅开发用）
    )