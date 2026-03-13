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
smarttutor/
├── app/
│   ├── __init__.py          # 应用包初始化
│   ├── config.py            # 配置文件
│   ├── models.py            # 数据模型定义
│   ├── prompts.py           # Prompt模板
│   └── main.py              # FastAPI主入口
├── agents/
│   ├── __init__.py          # Agents包初始化
│   ├── llm_client.py        # LLM客户端
│   ├── classifier.py        # 问题分类器
│   ├── guardrails.py        # 安全防护
│   ├── answer_generator.py  # 答案生成器
│   └── conversation.py      # 对话管理器
├── ui/
│   ├── __init__.py          # UI包初始化
│   └── gradio_app.py        # Gradio界面
├── tests/
│   └── test_examples.py    # 测试用例
├── requirements.txt          # 项目依赖
└── README.md               # 说明文档
```

---

## 🚀 快速开始

### 1. 克隆项目

```bash
cd /Users/nanchen/Documents/hkust/5900/project
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
cd smarttutor
pip install -r requirements.txt
```

### 4. 配置 API 密钥

编辑 `.env` 文件，添加您的 Azure OpenAI 配置：

```bash
# .env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**注意**: 你也可以使用标准 OpenAI API：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. 启动后端服务

```bash
cd smarttutor
python -m app.main
```

服务将在 `http://localhost:8000` 启动。

### 6. 启动前端界面（可选）

在另一个终端中运行：

```bash
cd smarttutor
python -m ui.gradio_app
```

前端将在 `http://localhost:7860` 启动。

---

## 📖 使用说明

### 通过 Web 界面

1. 打开浏览器访问 `http://localhost:7860`
2. 在输入框中输入您的问题
3. 点击"发送"或按回车提交

### 通过 API

```bash
# 发送聊天请求
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "平方根1000是有理数吗？"}'

# 获取对话历史
curl "http://localhost:8000/conversation/{session_id}/history"

# 获取对话总结
curl "http://localhost:8000/conversation/{session_id}/summary"

# 健康检查
curl "http://localhost:8000/health"
```

---

## 📝 示例对话

### 示例 1: 数学问题

```
用户: 平方根1000是有理数吗？
助手: 平方根1000不是有理数...
```

### 示例 2: 历史问题

```
用户: 谁是法国第一任总统？
助手: 法国第一任总统是路易-拿破仑·波拿巴...
```

### 示例 3: 年级适配

```
用户: 我是大学一年级的学生
助手: 好的，我已经记录您的年级为大一...
```

### 示例 4: 无效问题被拒绝

```
用户: 从香港去伦敦最好的出行方式是什么？
助手: 抱歉，我无法帮助回答这个问题，因为这不是一个数学或历史作业问题...
```

### 示例 5: 对话总结

```
用户: 总结我们的对话
助手: 对话总结: 我们讨论了数学和历史问题...
```

---

## 🧪 测试用例

项目包含以下测试用例（详见 `tests/test_examples.py`）：

| 用例ID | 问题类型 | 问题内容 | 预期结果 |
|--------|----------|----------|----------|
| TC001 | 数学 | 求解 x + 1 = 2 中的 x | valid_math |
| TC002 | 数学 | 平方根1000是有理数吗？ | valid_math |
| TC003 | 数学应用 | Beth烤了4批2打饼干... | valid_math |
| TC005 | 历史 | 谁是法国第一任总统？ | valid_history |
| TC006 | 历史 | 第二次世界大战什么时候开始？ | valid_history |
| TC007 | 无效 | 香港到伦敦最好的出行方式？ | 拒绝（非作业） |
| TC008 | 无效 | 在繁忙街道放鞭炮会怎样？ | 拒绝（非作业） |
| TC009 | 无效 | HKUST第一任校长是谁？ | 拒绝（过于小众） |
| TC010 | 功能 | 我是大学一年级学生 | 记录年级 |
| TC011 | 功能 | 总结对话 | 返回总结 |

---

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API密钥 | - |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 端点 | - |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | 部署名称 | gpt-4 |
| `AZURE_OPENAI_API_VERSION` | API版本 | 2024-02-15-preview |
| `OPENAI_API_KEY` | OpenAI API密钥（备选） | - |
| `DEBUG` | 调试模式 | true |
| `SESSION_TIMEOUT` | 会话超时时间（秒） | 3600 |

### 模型参数

在 `app/config.py` 中可以修改：

```python
MODEL_TEMPERATURE = 0.7      # 创造性程度
MODEL_MAX_TOKENS = 2000       # 最大token数
```

---

## 📋 提交要求（根据项目文档）

本项目满足以下提交要求：

1. ✅ **问题分类**: 准确识别数学/历史/无效问题
2. ✅ **有效问题回答**: 提供准确的作业解答
3. ✅ **无效问题拒绝**: 礼貌拒绝非作业问题
4. ✅ **多轮对话**: 支持追问和深入讲解
5. ✅ **年级适配**: 根据用户年级调整答案深度
6. ✅ **对话总结**: 支持请求总结功能

### 报告中包含的示例

根据项目要求，报告中包含至少5个示例：

**接受的有效问题（至少2个）：**
1. 数学：求解 x + 1 = 2 中的 x
2. 数学：平方根1000是有理数吗？
3. 历史：谁是法国第一任总统？

**拒绝的无效问题（至少2个）：**
1. 旅行建议：从香港去伦敦最好的出行方式？
2. 过于小众：HKUST第一任校长是谁？

**对话总结请求（至少1个）：**
- 总结我们的对话

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 对话框架
- [Azure OpenAI](https://azure.microsoft.com/services/cognitive-services/openai/) - LLM服务
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [Gradio](https://gradio.app/) - UI框架
