# app/main.py
# 应用入口 —— FastAPI 应用初始化、路由注册、中间件配置、启动命令

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 导入路由模块
from app.api.v1 import chat                                  # 聊天接口路由
from app.api.v1 import oss                                   # OSS 文件上传接口路由

# 导入日志配置
from app.common.logger import setup_logging


# ==================== 日志初始化 ====================
setup_logging()                                               # 在应用启动前初始化日志，确保后续所有模块的日志输出统一


# ==================== FastAPI 应用实例 ====================
app = FastAPI(
    title="Personal Chief API",                               # API 文档标题
    description="私厨——基于 AI 的智能菜谱推荐助手",                # API 文档描述
    version="0.1.0",                                          # 版本号
)


# ==================== CORS 跨域配置 ====================
# 允许前端（如 React、Vue）从不同域名/端口访问后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                                      # 允许所有来源（生产环境应限制为具体域名）
    allow_credentials=True,                                   # 允许携带 Cookie 等凭证信息
    allow_methods=["*"],                                      # 允许所有 HTTP 方法（GET、POST、DELETE 等）
    allow_headers=["*"],                                      # 允许所有请求头
)


# ==================== 路由注册 ====================
# 将 chat 和 oss 子路由挂载到 /api/v1 前缀下
app.include_router(chat.router, prefix="/api/v1")             # 聊天相关接口：/api/v1/chat/...
app.include_router(oss.router, prefix="/api/v1")              # OSS 相关接口：/api/v1/oss/...


# ==================== 静态文件服务 ====================
# 将 static 目录挂载为静态文件服务，前端可直接访问其中的图片、CSS、JS 等
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ==================== 前端页面入口 ====================
@app.get("/")
async def root():
    """
    访问根路径时返回前端首页（static/index.html）
    """
    return FileResponse("app/static/index.html")


# ==================== 启动入口 ====================
if __name__ == "__main__":
    import uvicorn
    # 启动命令：python -m app.main 或 python app/main.py
    uvicorn.run(
        "app.main:app",                                  # 模块路径:应用实例名
        host="127.0.0.1",                                     # 监听地址（本地）
        port=8001,                                            # 监听端口
        reload=True                                           # 开发模式：代码变更时自动重启
    )