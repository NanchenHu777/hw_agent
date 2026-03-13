# SmartTutor - 作业辅导智能体
# 测试用例
"""
SmartTutor - 测试用例
"""
# 测试用例定义
TEST_CASES = {
    # 有效的数学问题
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
    
    # 有效的历史问题
    "TC005": {
        "question": "谁是法国第一任总统？",
        "expected_category": "valid_history",
        "description": "历史人物"
    },
    "TC006": {
        "question": "第二次世界大战什么时候开始？",
        "expected_category": "valid_history",
        "description": "历史事件时间"
    },
    
    # 无效问题 - 非作业相关
    "TC007": {
        "question": "从香港去伦敦最好的出行方式是什么？",
        "expected_category": "invalid",
        "reason": "非作业问题 - 旅行建议",
        "description": "旅行相关"
    },
    "TC008": {
        "question": "如果在繁忙的街道上放鞭炮会发生什么？",
        "expected_category": "invalid",
        "reason": "非作业问题",
        "description": "常识问题"
    },
    
    # 无效问题 - 过于小众
    "TC009": {
        "question": "香港科技大学的第一任校长是谁？",
        "expected_category": "invalid",
        "reason": "过于小众的本地问题",
        "description": "本地大学历史"
    },
    
    # 功能测试 - 年级适配
    "TC010": {
        "question": "我是一名大学一年级学生",
        "expected_intent": "grade_info",
        "description": "年级信息输入"
    },
    
    # 功能测试 - 对话总结
    "TC011": {
        "question": "请总结我们的对话",
        "expected_intent": "summarize",
        "description": "对话总结请求"
    },
    
    # 超出范围的问题
    "TC012": {
        "question": "如何用Python编写一个排序算法？",
        "expected_category": "invalid",
        "reason": "超出学科范围",
        "description": "编程问题"
    }
}
# 示例对话流程
SAMPLE_CONVERSATION = [
    {
        "role": "assistant",
        "content": "欢迎使用SmartTutor！我是您的数学和历史作业辅导老师。请问有什么可以帮助您的？"
    },
    {
        "role": "user", 
        "content": "我是大学一年级的学生"
    },
    {
        "role": "assistant",
        "content": "好的，我已经记录您的年级为大一。在后续的解答中，我会根据大学一年级的知识水平来调整答案的深度。请问您有什么数学或历史问题需要帮助吗？"
    },
    {
        "role": "user",
        "content": "平方根1000是有理数吗？"
    },
    {
        "role": "assistant",
        "content": "平方根1000不是有理数。\n\n让我解释一下：\n\n1. 首先，1000 = 10³ = 2³ × 5³\n\n2. 1000的平方根是 √1000 = 10√10 ≈ 31.62\n\n3. 有理数是可以表示为两个整数之比的数。√10不能表示为两个整数的比值，因为它是一个无理数。\n\n4. 一个数如果不能写成两个整数的比值，就是无理数。√10是无理数，因此√1000 = 10√10也是无理数。"
    },
    {
        "role": "user",
        "content": "谁是法国第一任总统？"
    },
    {
        "role": "assistant", 
        "content": "法国第一任总统是路易-拿破仑·波拿巴（Louis-Napoléon Bonaparte）。\n\n他在1848年12月20日当选为法兰西第二共和国总统，后来在1852年称帝，建立法兰西第二帝国，成为拿破仑三世。\n\n这是法国历史上的第一个总统职位。"
    },
    {
        "role": "user",
        "content": "总结我们的对话"
    }
]
def print_test_cases():
    """打印测试用例"""
    print("=" * 60)
    print("SmartTutor 测试用例")
    print("=" * 60)
    
    for tc_id, tc in TEST_CASES.items():
        print(f"\n{tc_id}: {tc['description']}")
        print(f"  问题: {tc['question']}")
        print(f"  预期分类: {tc.get('expected_category', 'N/A')}")
        if 'reason' in tc:
            print(f"  预期原因: {tc['reason']}")
        if 'expected_intent' in tc:
            print(f"  预期意图: {tc['expected_intent']}")
if __name__ == "__main__":
    print_test_cases()
