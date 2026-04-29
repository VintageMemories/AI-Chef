# AI Chef 🧑‍🍳

**基于 LangGraph 多智能体框架的智能私厨助手**，采用阿里云百炼千问大模型与 Tavily 搜索引擎，上传食材照片或输入食材清单，自动推荐营养丰富且制作简单的菜谱。

---

## ✨ 核心功能

1. **食材识别与智能搜索**  
   - 支持上传食材图片或手动输入食材清单。  
   - 调用 Tavily 搜索引擎实时检索菜谱，附带图片参考。

2. **评分排序**  
   - 从营养价值和制作难度两个维度打分，简单且营养高的排前面。

3. **多轮对话与流式输出**  
   - 基于 LangGraph 的多轮对话，支持 SSE 流式输出和 Markdown 渲染。

4. **会话记忆**  
   - 基于 SQLite + SqliteSaver 的对话持久化，支持历史消息查询与清空。

5. **OSS 直传**  
   - 图片通过预签名 URL 直传阿里云 OSS，不占用服务器带宽。

6. **现代化前端**  
   - 响应式聊天界面，图片预览、打字动画、移动端适配。

---

## 📁 目录结构

```plaintext
AI Chef/
├── app/                                # 后端核心代码
│   ├── main.py                         # FastAPI 启动入口
│   ├── agents/
│   │   └── ai_chef.py                  # AI 厨师 Agent（模型初始化、工具绑定、会话持久化）
│   ├── api/v1/
│   │   ├── chat.py                     # 聊天接口（流式对话、历史消息）
│   │   └── oss.py                      # OSS 接口（预签名上传）
│   ├── common/
│   │   └── logger.py                   # 全局日志配置
│   ├── models/
│   │   └── schemas.py                  # Pydantic 数据模型
│   ├── db/                             # SQLite 数据库目录
│   └── static/
│       └── index.html                  # 前端聊天界面
├── langgraph.json                      # LangGraph 配置文件
├── pyproject.toml                      # 项目依赖配置
└── .env                                # 环境变量（需自行创建）
```

---

## 🚀 快速开始

### 环境要求

- Python >= 3.11  
- Git  
- uv  

### 本地运行

1. **克隆仓库**  
   ```bash
   git clone https://github.com/VintageMemories/AI-Chef.git
   cd AI-Chef
   ```

2. **安装依赖**  
   ```bash
   uv sync
   ```

3. **配置环境变量**  
   在项目根目录创建 `.env` 文件，并填入以下内容：  
   ```plaintext
   # 百炼 API Key
   DASHSCOPE_API_KEY=sk-你的Key

   # Tavily API Key
   TAVILY_API_KEY=你的Tavily Key

   # LangSmith API Key（可选）
   LANGSMITH_API_KEY=

   # 阿里云 OSS
   OSS_ACCESS_KEY_ID=你的AccessKey ID
   OSS_ACCESS_KEY_SECRET=你的AccessKey Secret
   OSS_BUCKET=agent-chef
   OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
   ```

4. **启动服务**  
   ```bash
   uv run langgraph dev
   ```  
   或直接运行：  
   ```bash
   uv run python app/main.py
   ```  
   启动成功后访问：  
   [http://127.0.0.1:8001](http://127.0.0.1:8001)

---

## 📡 API 接口

| 方法   | 路径                | 说明         |
|--------|---------------------|--------------|
| POST   | `/api/v1/chat/stream`    | 流式对话     |
| GET    | `/api/v1/chat/messages`  | 获取历史消息 |
| DELETE | `/api/v1/chat/messages`  | 清空历史消息 |
| GET    | `/api/v1/oss/presign`    | 获取 OSS 上传预签名 URL |

---

## 📝 运行流程

1. 用户上传食材照片或输入食材清单  
2. Agent 识别食材并调用 Tavily 搜索相关菜谱  
3. Agent 从营养价值和制作难度两个维度评估排序  
4. 结构化输出推荐结果：菜谱名称、得分、推荐理由、参考图片  

---

## 🛠️ 技术栈

| 层级       | 技术                                  |
|------------|-------------------------------------|
| 前端       | HTML5, CSS3, JavaScript (原生)       |
| 后端       | FastAPI (Python)                     |
| 大模型     | 阿里云百炼 DashScope（千问 Qwen3.6-Plus） |
| Agent 框架 | LangGraph                           |
| 搜索工具   | Tavily Search                      |
| 对话记忆   | LangGraph SqliteSaver + SQLite       |
| 文件存储   | 阿里云 OSS                           |
| 依赖管理   | uv                                  |

---

## 🔗 相关��源

- 阿里云百炼 DashScope: https://dashscope.aliyun.com/  
- LangGraph 文档: https://langchain-ai.github.io/langgraph/  
- Tavily Search: https://tavily.com/  
- 阿里云 OSS 文档: https://help.aliyun.com/product/31815.html  

---

## 👤 作者信息

- **GitHub**: [@VintageMemories](https://github.com/VintageMemories)  
- **许可证**: MIT License
