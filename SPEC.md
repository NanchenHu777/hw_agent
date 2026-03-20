# SmartTutor - 作业辅导智能体实现计划

# 321ver
**改动说明**

这次优化是在不大改架构的前提下完成的，目标是把现有初版提升到“更可靠、更一致、可证明”的状态，重点围绕作业要求中的 `math/history`、`guardrails`、`multi-turn`、`summary` 和“如何证明做对了”这几件事展开。

**1. 总体原则**
- 先在新分支上开发和保存，分支名是 `feat/reliability-guardrails-polish`。
- 保留原有 `Triage -> Guardrail -> AnswerGenerator -> Conversation` 结构，不做重构式改写。
- 优先修“行为不一致、容易误判、难以验证”的问题。
- 测试采用 `mock-first`，只做少量真实 smoke test，尽量节省 token。

**2. 架构与流程层的改动**
主要修改了这几处：
- [orchestrator.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/orchestrator.py)
- [main.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/app/main.py)
- [gradio_app.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/ui/gradio_app.py)

做了这些调整：
- 统一入口：Gradio UI 不再自己复制一套 `guardrail + triage` 逻辑，而是统一调用 orchestrator，保证 UI 和 API 行为一致。
- 固定处理顺序：先处理 `grade_info`，再处理 `summarize`，之后才进入 guardrail 和学科回答。
- `/chat` 响应补齐 `reason` 字段，方便展示“为什么接受/拒答”。

**3. 稳定性修复**
主要改了：
- [conversation.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/conversation.py)
- [llm_client.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/llm_client.py)
- [multi_model_client.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/multi_model_client.py)

修复内容：
- 修复 session 不存在时 `add_message` / `set_grade` 的创建逻辑，避免空 session 访问问题。
- 修复 LangChain 导入兼容问题，消除测试中的导入失败。
- 修复数学模型权限问题：当专用数学模型无权限时，自动回退到默认模型，不再直接 401 报错。

**4. 规则与判定逻辑优化**
主要修改：
- [triage_agent.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/triage_agent.py)
- [guardrail_agent.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/guardrail_agent.py)
- [prompts.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/app/prompts.py)

改动重点：
- fallback 规则补强：短问题、明显数学/历史题、年级信息、summary 请求都能稳定兜底。
- 新增 `小学生 / 小学 / primary school / elementary school` 年级识别。
- 新增 `calculus / 微分 / 积分` 等数学关键词识别。
- 放宽作业问题定义：数学/历史中的“概念解释、背景说明、证明思路”也算有效作业问题，不要求一定是纯算式题。
- 对已经被 triage 判为 `valid_math/valid_history` 的问题，不再让第二个 LLM guardrail 再次随机否决；这一步只保留显式规则拦截，比如危险内容、本地小众、明显越界。

**5. “低年级 + 高阶问题”场景修复**
这是后面专门排查并整体修掉的一组问题，主要修改：
- [answer_generator.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/answer_generator.py)
- [prompts.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/app/prompts.py)
- [triage_agent.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/triage_agent.py)
- [orchestrator.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/orchestrator.py)

根因有两层：
- `triage/guardrail` 会把“解释微积分”“求导数”这类题误判为非作业。
- 即使已经放行，`answer_generator` 也可能因为“用户是小学生”而直接拒答高阶内容。

对应修复：
- `triage` 增加“明显数学/历史题救回”逻辑。
- `orchestrator` 改成“已接收的学科题只走显式规则 guardrail”。
- `answer_generator` 明确要求“超纲也要降难度解释，不能直接拒答”。
- 如果模型第一次仍然因为“年级低/内容太难”而拒答，会自动重试一次，强制改成简化解释。

修完后的真实效果是：
- `我是小学生` 可以正确记录。
- `请解释一下微积分` 不再被拒答，而是给简化解释。
- `求 x^2 的导数是多少？` 不再直接拒答，会说明这是进阶内容，并给出 `2x` 这个结果。

**6. 多轮追问与闲聊边界修复**
这是后续真实对话测试里暴露出来的第二组问题，主要修改：
- [conversation.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/conversation.py)
- [orchestrator.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/orchestrator.py)
- [triage_agent.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/agents/triage_agent.py)

新增和修复的点包括：
- 为 session 增加 `last_response_kind`，记录上一轮成功回答的类型。
- 新增短追问上下文继承规则，支持 `and more?`、`explain more`、`why?`、`how?` 这类短句自动接回上一轮数学/历史上下文。
- 新增简单闲聊识别与礼貌回复，支持 `hi`、`thank you`、`bye`、`That’s helpful, thank you.` 这类输入不再误走拒答链路。
- 修复一个由此带出的回归：并不是所有被模型打成 `chit_chat` 的输入都应该直接放行。像旅行建议、危险问题这类即使被误标成 `chit_chat`，也仍然必须继续走 guardrail 并明确拒答。

修完后的真实效果是：
- `Who was the first president of France? -> And more?` 会继续历史解释，而不是拒答。
- `That’s helpful, thank you.` 会返回 `You're welcome.`，不会再被误拒。
- `How do I get to London?` 即使某次分类结果偏向 `chit_chat`，最终仍会正确拒答。

**7. 自动化测试补强**
新增或完善了这些测试文件：
- [test_api.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/test_api.py)
- [test_agents.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/test_agents.py)
- [test_examples.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/tests/test_examples.py)
- [test_fallback_rules.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/tests/test_fallback_rules.py)
- [test_multiturn_followups.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/tests/test_multiturn_followups.py)
- [test_ui.py](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/tests/test_ui.py)
- [TESTING.md](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/tests/TESTING.md)

覆盖范围包括：
- math/history 正常接受
- 非作业、危险、小众本地问题拒答
- grade_info 与 summary 特殊路径
- UI/API 行为一致
- 多轮追问与澄清场景
- `小学生 + 高阶数学` 场景
- 简单 chit-chat 的礼貌回复
- chit-chat 与真正拒答场景的边界
- 模型权限回退
- “模型因年级低而拒答”时的自动重试

**8. 英文化与提交材料补强**
这部分是为了最终提交而补的文档工作，主要修改：
- [README.md](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/README.md)
- [REPORT.md](/d:/HKUST/Artificial%20Intelligent/project/hw_agent_319_v2/smarttutor/REPORT.md)
- `smarttutor/app` 与 `smarttutor/agents` 下的注释和 docstring

具体改动：
- README 改为完整英文版，并且只围绕 active agent pipeline 解释总体和细节设计思路，不再把 UI 作为架构重点。
- 新增纯英文 `REPORT.md`，可直接作为不超过 2 页 PDF 的报告草稿基础。
- 代码注释和文档字符串统一改为英文，但功能性中文关键词保留，保证中英文兼容 fallback 不被破坏。

**9. 验证结果**
当前全量测试结果：
```text
37 passed in 6.61s
```

并且做了真实 smoke test，确认以下链路已经正常：
- 单轮数学题
- 单轮历史题
- 非作业拒答
- summary
- 小学生 + 微积分解释
- 小学生 + 简单导数题
- 短历史追问 `And more?`
- 简单礼貌闲聊 `Hi` / `That’s helpful, thank you.`

**10. 提交记录**
本轮相关提交包括：
- `3cb0ab2` `chore: baseline before reliability polish`
- `7f047e2` `fix: unify tutoring flow and fallback guardrails`
- `83d6f44` `test: add reliability regression coverage`
- `d2deb33` `fix: fallback when task model access is denied`
- `3b975b6` `test: add multi-turn and boundary coverage`
- `8ffd8fd` `test: cover primary school advanced math scenario`
- `1ef6e94` `fix: handle advanced math across grade levels`
- `75a5ec1` `feat: switch default UX to English`
- `ed70eb7` `fix: carry context across short follow-up prompts`
- `11642ff` `fix: allow simple chit-chat without rejection`
- `129209f` `docs: add end-to-end dialogue smoke test`
- `85eeee7` `fix: narrow chit-chat bypass and simplify demo dialogue`
- `02f3f1e` `docs: rewrite english agent documentation and report`

**11. 当前结论**
这次改动的核心成果不是“功能变多了”，而是把系统从“能跑”提升成了“流程一致、规则更稳、关键场景可测、真实结果更贴合作业要求”。尤其是下面这几项，已经明显更符合老师要求：
- 数学和历史都能处理
- 有明确 guardrails
- 支持多轮与总结
- 能识别类似 `and more?`、`why?` 这类继续上下文意图并回答
- 能根据年级调整回答
- 超纲问题不会简单拒答，而是尽量简化解释
- 简单 chit-chat 不会误拒，但旅行/危险问题也不会因为被误标成 `chit_chat` 而漏拦截
- 有自动化测试、真实 smoke test、英文 README 和英文报告草稿作为可靠性证据

如果你要，我可以把这份说明再压缩成“报告版 1 页中文总结”。



# main ver

## 1. 项目概述

### 项目名称
**SmartTutor** - 多轮对话作业辅导智能体

### 项目目标
设计并实现一个基于LLM的多轮对话作业辅导系统，专注于数学和历史学科的作业问题解答，具备可靠性和安全防护机制。

### 核心技术栈
- **LLM API**: Azure OpenAI (GPT-4) 或 genai.ust.hk
- **对话框架**: LangChain
- **后端**: FastAPI
- **前端**: Gradio (简洁易用的Web UI)
- **部署**: 本地运行

---

## 2. 功能需求分析

### 2.1 核心功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 问题分类 | 识别用户问题为数学/历史/无效 | P0 |
| 回答有效问题 | 对数学和历史问题提供准确解答 | P0 |
| 拒绝无效问题 | 礼貌拒绝非作业相关问题 | P0 |
| 多轮对话 | 支持追问和深入讲解 | P0 |
| 年级适配 | 根据用户年级调整答案深度 | P1 |
| 对话总结 | 总结当前对话内容 | P1 |

### 2.2 问题分类标准

#### 有效问题 (Accepted)
- **数学**: 代数、几何、微积分、概率、统计等学科问题
- **历史**: 历史事件、人物、年代等相关问题

#### 无效问题 (Rejected)
- 非作业相关问题（如旅行建议、生活问题）
- 超出学科范围的问题
- 过于小众/本地化的问题（如某所本地大学的校长）
- 危险或不当问题

### 2.3 用户意图识别

| 意图 | 处理方式 |
|------|----------|
| 提问作业问题 | 正常回答 |
| 询问非作业问题 | 礼貌拒绝 |
| 要求总结对话 | 执行总结功能 |
| 告知年级信息 | 记录并适配 |
| 其他闲聊 | 引导回到学习话题 |

---

## 3. 系统架构设计

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Gradio Web UI)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Input      │  │  Conversation│  │    Output     │      │
│  │  Processing  │  │   Manager    │  │  Formatter    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
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

### 3.2 模块设计

#### 模块1: QuestionClassifier
- **职责**: 分类用户问题为有效/无效，识别学科
- **输入**: 用户问题文本
- **输出**: 分类结果 (valid_math, valid_history, invalid)

#### 模块2: AnswerGenerator  
- **职责**: 生成问题的回答
- **输入**: 问题、学科、年级、对话上下文
- **输出**: 结构化的回答

#### 模块3: ConversationManager
- **职责**: 管理对话历史和上下文
- **功能**: 
  - 存储对话历史
  - 提取用户年级信息
  - 提供对话总结功能

#### 模块4: Guardrails
- **职责**: 安全防护，检查问题是否合规
- **功能**:
  - 检测无效问题
  - 提供拒绝理由

---

## 4. 详细实现计划

### 阶段1: 项目基础搭建

#### 1.1 创建项目结构
```
smarttutor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI主入口
│   ├── config.py            # 配置文件
│   ├── prompts.py           # Prompt模板
│   └── models.py            # 数据模型
├── agents/
│   ├── __init__.py
│   ├── classifier.py        # 问题分类器
│   ├── answer_generator.py  # 答案生成器
│   ├── guardrails.py         # 安全防护
│   └── conversation.py       # 对话管理器
├── ui/
│   └── gradio_app.py        # Gradio界面
├── tests/
│   └── test_examples.py     # 测试用例
├── requirements.txt          # 依赖
├── .env.example             # 环境变量示例
└── README.md               # 说明文档
```

#### 1.2 配置文件 (config.py)
- Azure OpenAI API配置
- 模型参数配置
- 系统提示词配置

### 阶段2: 核心功能实现

#### 2.1 问题分类器 (classifier.py)
- 使用LLM进行Zero-shot分类
- 定义分类prompt，包含示例
- 输出结构化JSON结果

#### 2.2 答案生成器 (answer_generator.py)
- 根据学科选择不同的回答策略
- 集成年级适配
- 支持多轮上下文

#### 2.3 安全防护 (guardrails.py)
- 定义无效问题类型
- 提供礼貌拒绝模板
- 支持自定义拒绝理由

#### 2.4 对话管理 (conversation.py)
- 使用LangChain Memory
- 支持上下文窗口
- 提供总结功能

### 阶段3: UI和集成

#### 3.1 FastAPI后端
- RESTful API接口
- 会话管理
- 错误处理

#### 3.2 Gradio前端
- 简洁美观的聊天界面
- 支持Markdown渲染
- 对话历史展示

### 阶段4: 测试和文档

#### 4.1 测试用例
至少包含：
- 2个有效数学问题
- 2个有效历史问题
- 2个无效问题（不同原因）
- 1个对话总结请求
- 1个年级适配示例

#### 4.2 文档
- README安装说明
- API使用文档
- 示例对话

---

## 5. Prompt工程设计

### 5.1 系统提示词 (System Prompt)

```
你是一位专业的作业辅导老师，名为SmartTutor。你的职责是帮助学生解决数学和历史作业问题。

## 你的能力
- 精通数学：代数、几何、微积分、概率、统计等
- 精通历史：世界历史、中国历史、各类历史事件和人物

## 回答规则
1. 只回答数学和历史相关的作业问题
2. 根据用户的年级调整答案的深度和详细程度
3. 提供清晰、准确、有教育意义的解答
4. 如果用户追问，要在前面的回答基础上继续深入

## 拒绝规则
对于以下问题，你需要礼貌拒绝：
- 非作业相关的问题（如旅行建议、生活问题）
- 超出数学和历史范围的问题
- 过于小众或本地化的问题
- 危险或不当的问题

拒绝时使用格式：抱歉，我无法帮助回答这个问题，因为[理由]。如果您有数学或历史作业问题，我很乐意帮助您。

## 对话管理
- 如果用户要求总结对话，请提取关键信息和已解决的问题
- 如果用户告知年级，请记住并在后续回答中适配
```

### 5.2 问题分类提示词

```
请分析以下问题，并将其分类。

问题: {user_question}

请从以下类别中选择一个：
- valid_math: 有效的数学作业问题
- valid_history: 有效的历史作业问题  
- invalid: 无效问题（非作业相关、超出范围等）

同时判断用户的意图：
- ask_question: 提问问题
- summarize: 要求总结对话
- grade_info: 告知年级信息
- chit_chat: 闲聊

请以JSON格式输出：
{{
  "category": "类别",
  "intent": "意图",
  "reason": "分类理由（如果invalid，说明原因）"
}}
```

---

## 6. API接口设计

### 6.1 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/chat` | POST | 发送消息，获取回复 |
| `/conversation/{session_id}/summary` | GET | 获取对话总结 |
| `/conversation/{session_id}/history` | GET | 获取对话历史 |
| `/health` | GET | 健康检查 |

### 6.2 请求/响应格式

#### Chat请求
```json
{
  "message": "用户消息",
  "session_id": "可选的会话ID"
}
```

#### Chat响应
```json
{
  "response": "助手的回复",
  "session_id": "会话ID",
  "category": "问题分类",
  "intent": "用户意图"
}
```

---

## 7. 测试用例设计

### 7.1 有效问题示例

| 用例ID | 问题类型 | 问题内容 | 预期分类 |
|--------|----------|----------|----------|
| TC001 | 数学 | 求解 x + 1 = 2 中的 x | valid_math |
| TC002 | 数学 | 平方根1000是有理数吗？ | valid_math |
| TC003 | 历史 | 谁是法国第一任总统？ | valid_history |
| TC004 | 数学应用 | Beth烤了4批2打饼干... | valid_math |

### 7.2 无效问题示例

| 用例ID | 问题内容 | 拒绝原因 |
|--------|----------|----------|
| TC005 | 香港到伦敦最好的出行方式？ | 非作业问题 |
| TC006 | 在繁忙街道放鞭炮会怎样？ | 非作业问题 |
| TC007 | HKUST第一任校长是谁？ | 过于小众 |

### 7.3 功能测试

| 用例ID | 测试内容 | 预期结果 |
|--------|----------|----------|
| TC008 | 用户说"我是大一学生" | 记录年级，后续回答适配 |
| TC009 | 用户要求"总结对话" | 返回对话总结 |
| TC010 | 多轮追问 | 正确理解上下文 |

---

## 8. 实施里程碑

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| Phase 1 | 项目搭建、依赖安装 | 1天 |
| Phase 2 | 核心功能实现（分类器、答案生成） | 2天 |
| Phase 3 | 对话管理和Guardrails | 1天 |
| Phase 4 | UI界面开发 | 1天 |
| Phase 5 | 测试和文档 | 1天 |

---

## 9. 验收标准

### 功能验收
- [ ] 能够正确分类数学/历史/无效问题
- [ ] 有效问题能得到准确答案
- [ ] 无效问题被礼貌拒绝
- [ ] 支持多轮对话和追问
- [ ] 年级适配功能正常
- [ ] 对话总结功能正常

### 测试验收
- [ ] 至少5个测试用例通过
- [ ] 包含数学、历史、无效问题示例
- [ ] 包含对话总结示例

### 文档验收
- [ ] README包含安装说明
- [ ] 代码有适当注释
- [ ] 包含运行示例
