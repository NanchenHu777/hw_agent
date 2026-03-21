# SmartTutor - 作业辅导智能体
# 测试用例
"""
SmartTutor - 测试用例

包含所有 PDF 要求的功能测试：
1. 有效数学问题
2. 有效历史问题
3. 拒绝的问题（多种原因）
4. 年级适配
5. 练习题生成
6. 对话总结
"""
# 测试用例定义
TEST_CASES = {
    # ============ 有效数学问题 ============
    "TC001": {
        "question": "求解 x + 1 = 2 中的 x",
        "expected_category": "valid_math",
        "description": "基础代数方程求解"
    },
    "TC002": {
        "question": "平方根1000是有理数吗？",
        "expected_category": "valid_math",
        "description": "无理数判断"
    },
    "TC003": {
        "question": "Beth烤了4批，每批2打饼干。如果这些饼干平均分给16个人，每个人能分到多少块饼干？",
        "expected_category": "valid_math",
        "description": "应用题 - 饼干分配"
    },
    "TC004": {
        "question": "如何计算两个城市之间的距离？",
        "expected_category": "valid_math",
        "description": "数学概念问题"
    },
    "TC005": {
        "question": "如何求解二次方程 x² - 5x + 6 = 0？",
        "expected_category": "valid_math",
        "description": "二次方程求解"
    },

    # ============ 有效历史问题 ============
    "TC006": {
        "question": "谁是法国第一任总统？",
        "expected_category": "valid_history",
        "description": "历史人物"
    },
    "TC007": {
        "question": "第二次世界大战什么时候开始？",
        "expected_category": "valid_history",
        "description": "历史事件时间"
    },
    "TC008": {
        "question": "法国大革命的主要人物有哪些？",
        "expected_category": "valid_history",
        "description": "历史人物与事件"
    },

    # ============ 无效问题 - 非作业相关 ============
    "TC009": {
        "question": "从香港去伦敦最好的出行方式是什么？",
        "expected_category": "invalid",
        "reason": "非作业问题 - 旅行建议",
        "description": "旅行相关"
    },
    "TC010": {
        "question": "今天天气怎么样？",
        "expected_category": "invalid",
        "reason": "非作业问题 - 天气",
        "description": "天气问题"
    },
    "TC011": {
        "question": "推荐一部好看的电影",
        "expected_category": "invalid",
        "reason": "非作业问题 - 娱乐",
        "description": "娱乐推荐"
    },

    # ============ 无效问题 - 超出范围 ============
    "TC012": {
        "question": "如何用Python编写一个排序算法？",
        "expected_category": "invalid",
        "reason": "超出学科范围 - 编程",
        "description": "编程问题"
    },
    "TC013": {
        "question": "什么是光的折射定律？",
        "expected_category": "invalid",
        "reason": "超出学科范围 - 物理",
        "description": "物理问题"
    },

    # ============ 无效问题 - 过于小众 ============
    "TC014": {
        "question": "香港科技大学的第一任校长是谁？",
        "expected_category": "invalid",
        "reason": "过于小众的本地问题",
        "description": "本地大学历史"
    },
    "TC015": {
        "question": "我家小镇上的第一家超市是什么时候开的？",
        "expected_category": "invalid",
        "reason": "过于小众的本地问题",
        "description": "本地化问题"
    },

    # ============ 无效问题 - 不当内容 ============
    "TC016": {
        "question": "如果在繁忙的街道上放鞭炮会发生什么？",
        "expected_category": "invalid",
        "reason": "可能涉及安全隐患",
        "description": "危险行为相关"
    },

    # ============ 功能测试 - 年级适配 ============
    "TC017": {
        "question": "我是一名大学一年级学生",
        "expected_intent": "grade_info",
        "description": "年级信息输入 - 大学"
    },
    "TC018": {
        "question": "我是高三学生",
        "expected_intent": "grade_info",
        "description": "年级信息输入 - 高中"
    },
    "TC019": {
        "question": "我正在读研二",
        "expected_intent": "grade_info",
        "description": "年级信息输入 - 研究生"
    },

    # ============ 功能测试 - 对话总结 ============
    "TC020": {
        "question": "请总结我们的对话",
        "expected_intent": "summarize",
        "description": "对话总结请求"
    },
    "TC021": {
        "question": "总结一下我们讨论的内容",
        "expected_intent": "summarize",
        "description": "对话总结请求（变体）"
    },

    # ============ 功能测试 - 练习题生成 ============
    "TC022": {
        "question": "给我出几道关于二次函数的练习题",
        "expected_category": "valid_math",
        "description": "练习题生成请求"
    },
    "TC023": {
        "question": "生成3道关于概率统计的练习题",
        "expected_category": "valid_math",
        "description": "练习题生成请求（指定数量）"
    },

    # ============ 追问场景 ============
    "TC024": {
        "question": "如何计算两个城市之间的距离？",
        "expected_category": "valid_math",
        "description": "追问场景 - 第一轮"
    },
    "TC025": {
        "question": "那如何找一个城市的中心点呢？",
        "expected_category": "valid_math",
        "description": "追问场景 - 第二轮（应理解上下文）"
    },

    # ============ 超出年级范围提示 ============
    "TC026": {
        "question": "请解释Peano算术",
        "expected_category": "valid_math",
        "description": "超出大一范围的数学概念"
    }
}


# 示例对话流程（符合 PDF 要求）
SAMPLE_CONVERSATION = [
    # 第1轮：助手欢迎
    {
        "role": "assistant",
        "content": "欢迎使用 SmartTutor！我是您的数学和历史作业辅导老师...\n\n## 我可以帮助您：\n- 解答数学作业问题\n- 解答历史作业问题\n- 提供解题思路和详细讲解\n- 生成练习题帮助您巩固知识"
    },
    # 第2轮：用户告知年级
    {
        "role": "user",
        "content": "我是一名大学一年级学生"
    },
    {
        "role": "assistant",
        "content": "好的，我已经记录您的年级信息为：大一。请问有什么数学或历史作业问题需要帮助？"
    },
    # 第3轮：数学问题
    {
        "role": "user",
        "content": "平方根1000是有理数吗？"
    },
    {
        "role": "assistant",
        "content": "平方根1000不是有理数...\n\n【提示】这是一个基础数学问题，适合巩固基础概念。\n\n让我解释一下...\n\n1. 首先，1000 = 10³ = 2³ × 5³\n2. √1000 = √(100 × 10) = 10√10 ≈ 31.62\n3. 因为√10不能表示为两个整数的比值，所以√1000是无理数。"
    },
    # 第4轮：历史问题
    {
        "role": "user",
        "content": "谁是法国第一任总统？"
    },
    {
        "role": "assistant",
        "content": "法国第一任总统是路易-拿破仑·波拿巴（Louis-Napoléon Bonaparte）。\n\n他在1848年12月20日当选为法兰西第二共和国总统...\n\n这是法国历史上的第一个总统职位。"
    },
    # 第5轮：旅行问题（被拒绝）
    {
        "role": "user",
        "content": "我想从香港去伦敦，最好的出行方式是什么？"
    },
    {
        "role": "assistant",
        "content": "抱歉，我无法帮助回答这个问题，因为这不是一个数学或历史作业问题。如果您有数学或历史作业问题，我很乐意帮助您。"
    },
    # 第6轮：过于小众的问题（被拒绝）
    {
        "role": "user",
        "content": "香港科技大学的第一任校长是谁？"
    },
    {
        "role": "assistant",
        "content": "抱歉，这个问题涉及的内容过于小众或本地化，不适合作为通用历史知识来回答。"
    },
    # 第7轮：危险行为问题（被拒绝）
    {
        "role": "user",
        "content": "如果在繁忙的街道上放鞭炮会发生什么？"
    },
    {
        "role": "assistant",
        "content": "抱歉，我无法帮助回答这个问题。请告诉我您需要解答的数学或历史作业问题。"
    },
    # 第8轮：练习题请求
    {
        "role": "user",
        "content": "给我出几道关于函数的练习题"
    },
    {
        "role": "assistant",
        "content": "好的，以下是关于函数的练习题：\n\n### 练习题\n\n**第1题** 已知 f(x) = 2x + 1，求 f(3)\n答案: f(3) = 7\n解析: 代入计算 f(3) = 2×3 + 1 = 7\n\n**第2题** ...\n\n**第3题** ..."
    },
    # 第9轮：对话总结
    {
        "role": "user",
        "content": "总结我们的对话"
    }
]


def print_test_cases():
    """打印测试用例"""
    print("=" * 70)
    print("SmartTutor 测试用例")
    print("=" * 70)

    categories = {
        "有效数学问题": [],
        "有效历史问题": [],
        "无效问题 - 非作业相关": [],
        "无效问题 - 超出范围": [],
        "无效问题 - 过于小众": [],
        "无效问题 - 不当内容": [],
        "年级适配": [],
        "对话总结": [],
        "练习题生成": [],
        "追问场景": []
    }

    for tc_id, tc in TEST_CASES.items():
        desc = tc["description"]
        if "数学" in tc.get("expected_category", "") or "math" in desc.lower():
            categories["有效数学问题"].append(tc_id)
        elif "history" in tc.get("expected_category", "").lower():
            categories["有效历史问题"].append(tc_id)
        elif tc.get("expected_intent") == "grade_info":
            categories["年级适配"].append(tc_id)
        elif tc.get("expected_intent") == "summarize":
            categories["对话总结"].append(tc_id)
        elif "练习题" in desc:
            categories["练习题生成"].append(tc_id)
        elif "追问" in desc:
            categories["追问场景"].append(tc_id)
        elif "非作业" in tc.get("reason", ""):
            categories["无效问题 - 非作业相关"].append(tc_id)
        elif "超出" in tc.get("reason", ""):
            categories["无效问题 - 超出范围"].append(tc_id)
        elif "小众" in tc.get("reason", ""):
            categories["无效问题 - 过于小众"].append(tc_id)
        elif "危险" in tc.get("reason", ""):
            categories["无效问题 - 不当内容"].append(tc_id)

    for category, cases in categories.items():
        if cases:
            print(f"\n【{category}】({len(cases)}题)")
            for tc_id in cases:
                tc = TEST_CASES[tc_id]
                print(f"  {tc_id}: {tc['description']}")
                print(f"    问题: {tc['question'][:50]}...")


def print_sample_conversation():
    """打印示例对话"""
    print("\n" + "=" * 70)
    print("示例对话流程")
    print("=" * 70)

    for i, msg in enumerate(SAMPLE_CONVERSATION):
        role = "AI" if msg["role"] == "assistant" else "用户"
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"\n{role}: {content}")


if __name__ == "__main__":
    print_test_cases()
    print_sample_conversation()
