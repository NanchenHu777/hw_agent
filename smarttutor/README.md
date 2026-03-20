# SmartTutor - 作业辅导智能体

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/LangChain-0.1+-green.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-orange.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Gradio-4.0+-pink.svg" alt="Gradio">
</p>

## 📚 项目简介

SmartTutor 是一个基于 LLM（大型语言模型）的多轮对话作业辅导智能体，专注于**数学**和**历史**学科的作业问题解答。

### 核心功能

- ✅ **问题分类**: 自动识别数学/历史/无效问题
- ✅ **智能回答**: 提供准确的作业问题解答
- ✅ **Guardrails**: 礼貌拒绝非作业相关问题
- ✅ **多轮对话**: 支持追问和深入讲解
- ✅ **年级适配**: 根据用户年级调整答案深度
- ✅ **对话总结**: 支持请求总结对话内容

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Gradio Web UI)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangChain Controller                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Question   │  │    Answer    │  │   Summary    │      │
│  │ Classifier   │  │   Generator  │  │   Generator  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (Azure OpenAI)                       │
│                    GPT-4 Turbo                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
hw_agent/
├── smarttutor/               # 主项目目录
│   ├── app/
│   │   ├── __init__.py          # 应用包初始化
│   │   ├── config.py            # 配置文件
│   │   ├── models.py            # 数据模型定义
│   │   ├── prompts.py           # Prompt模板
│   │   └── main.py              # FastAPI主入口
│   ├── agents/
│   │   ├── __init__.py          # Agents包初始化
│   │   ├── llm_client.py        # LLM客户端
│   │   ├── classifier.py        # 问题分类器
│   │   ├── guardrails.py        # 安全防护
│   │   ├── answer_generator.py  # 答案生成器
│   │   └── conversation.py      # 对话管理器
│   ├── ui/
│   │   ├── __init__.py          # UI包初始化
│   │   └── gradio_app.py        # Gradio界面
│   ├── tests/
│   │   └── test_examples.py    # 测试用例
│   ├── requirements.txt          # 项目依赖
│   ├── .env                     # 环境变量配置
│   └── README.md               # 说明文档
├── start.sh                    # 一键启动脚本
├── stop.sh                     # 一键停止脚本
└── logs/                       # 日志目录（自动创建）
```

---

## 🚀 快速开始

### 🚀 一键启动（推荐）

以下步骤适合没有编程经验的用户：只要按顺序复制粘贴命令即可。

1. 打开「终端（Terminal）」
2. 进入项目根目录（你克隆仓库后所在的文件夹）

```bash
cd hw_agent  # 如果你克隆到其它目录，请替换为对应路径
```

3. 让启动/停止脚本可执行（只需执行一次）

```bash
chmod +x ./start.sh ./stop.sh
```

4. 启动服务

```bash
./start.sh
```

启动脚本会自动执行以下流程：
- 🔍 检查并清理被占用的端口（默认使用 8000 & 7861）
- 🚀 启动后端 API 服务（http://localhost:8000）
- 🎨 启动前端 Gradio 界面（http://localhost:7861）
- ✅ 显示服务启动结果与访问地址

> 如果出现 `Permission denied`，请先运行 `chmod +x ./start.sh` 再重试。

### 🛑 停止服务（推荐）

在另一个终端窗口里执行：

```bash
cd hw_agent  # 如果你克隆到其它目录，请替换为对应路径
./stop.sh
```

> 如果你是在同一个终端运行的，也可以按 `Ctrl+C` 强制停止当前运行的服务。


---

## 📋 完整安装流程

### 1. 克隆项目

```bash
git clone https://github.com/NanchenHu777/hw_agent.git
cd hw_agent
```

### 2. 环境准备（必做）

本项目使用 Python 运行。请确认已安装 Python 3.8 或更高版本：

```bash
python --version
```

如果提示 `command not found`，请先安装 Python（macOS 可在官网下载安装，Windows 可在 https://www.python.org/downloads/ 下载安装）。

#### 2.1 创建并激活虚拟环境（推荐）

在项目根目录运行：

```bash
python -m venv venv
```

**激活虚拟环境**：

- macOS / Linux：
  ```bash
  source venv/bin/activate
  ```
- Windows (PowerShell)：
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- Windows (cmd)：
  ```cmd
  venv\Scripts\activate
  ```

激活后，你会看到命令行提示符前出现 `(venv)`，表示依赖将安装到隔离环境中。

### 3. 安装依赖

在虚拟环境激活状态下运行：

```bash
pip install -r requirements.txt
```

如果安装过程中报错，通常是因为缺少系统组件（如 `gcc`、`curl` 等），请根据错误提示安装对应依赖。通常 macOS 可以运行：

```bash
xcode-select --install
```

### 4. 配置 API 密钥

编辑 `.env` 文件，添加您的 Azure OpenAI 配置：

```bash
# .env
HKUST_AZURE_API_KEY=your_api_key_here
HKUST_AZURE_ENDPOINT=https://hkust.azure-api.net
HKUST_AZURE_API_VERSION=2025-02-01-preview

# 模型选择
MATH_MODEL=gpt-4o-mini
HISTORY_MODEL=gpt-4o
DEFAULT_MODEL=gpt-4o-mini
```

**注意**: 你也可以使用标准 OpenAI API：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. 启动服务

#### 方式一：一键启动（推荐）
```bash
cd ..  # 返回项目根目录
./start.sh
```

#### 方式二：手动启动

**启动后端服务**：
```bash
cd smarttutor
python -m app.main
```

**启动前端界面**（另一个终端）：
```bash
cd smarttutor
python -m ui.gradio_app
```

---

## 📖 Usage

### Via the Web UI

1. Open your browser and visit `http://localhost:7861`
2. Type your question into the input box
3. Click "Send" or press Enter to submit

### Via the API

```bash
# Send a chat request
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Is square root of 1000 rational?"}'

# Get conversation history
curl "http://localhost:8000/conversation/{session_id}/history"

# Get a conversation summary
curl "http://localhost:8000/conversation/{session_id}/summary"

# Health check
curl "http://localhost:8000/health"
```

---

## 📝 Example Dialogues

### Example 1: Math Question

```
User: Is square root of 1000 rational?
Assistant: Square root of 1000 is not a rational number...
```

### Example 2: History Question

```
User: Who was the first president of France?
Assistant: The first president of France was Louis-Napoleon Bonaparte...
```

### Example 3: Grade Adaptation

```
User: I am a first-year university student.
Assistant: Thanks. I've recorded your grade level as first-year university student...
```

### Example 4: Rejected Invalid Question

```
User: What's the weather like today?
Assistant: Sorry, I can't help with that because it is not a math or history homework question...
```

### Example 5: End-to-End Multi-Turn Smoke Test

Use a single session and send the following turns in order. Exact wording may vary, but the behavior should remain consistent. This shorter dialogue is designed for the report and demo: it includes at least two accepted questions, two rejected questions, one summary request, and three highlight edge cases: short contextual follow-up, low-grade advanced math, and polite chit-chat.

```text
Assistant: Welcome to SmartTutor, your homework tutor for math and history. What can I help you with today?

User: Hi
Assistant: A brief greeting. It should not reject the message.

User: x+1=2
Assistant: Accept as math and solve it.

User: Why subtract 1 on both sides?
Assistant: Continue the same math context instead of rejecting the follow-up.

User: Who was the first president of France?
Assistant: Accept as history and answer correctly.

User: And more?
Assistant: Continue the previous history context rather than rejecting the short follow-up.

User: How do I get to London?
Assistant: Politely reject because this is travel advice, not math or history homework.

User: Who was HKUST's first president?
Assistant: Reject because it is too local or niche for the intended history-homework scope.

User: I am a primary school student.
Assistant: Update the stored grade level.

User: What is the derivative of x^2?
Assistant: Do not reject. Give a simplified explanation suitable for a younger student.

User: That's helpful, thank you.
Assistant: You're welcome.

User: Summarize our conversation so far.
Assistant: Return a summary covering accepted topics and rejected categories.
```

---

## 🔧 开发与调试

### 运行测试

```bash
cd smarttutor
python -m pytest
```

### 查看日志

启动脚本会自动创建日志文件：
- `logs/backend.log` - 后端服务日志
- `logs/frontend.log` - 前端服务日志

### 常见问题

**Q: 端口被占用怎么办？**
A: 使用 `./start.sh` 脚本，它会自动清理端口冲突。

**Q: 如何更换 LLM 提供商？**
A: 编辑 `.env` 文件，修改相应的 API 配置。

**Q: 如何添加新的学科支持？**
A: 在 `agents/classifier.py` 中添加新的分类规则，在 `agents/answer_generator.py` 中添加对应的回答逻辑。

---

## 📄 许可证

本项目仅用于学习和研究目的。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<p align="center">Made with ❤️ for better education</p>
