"""
SmartTutor - 测试脚本
验证重构后的 Agent 系统
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_triage_agent():
    """测试 Triage Agent"""
    from agents.triage_agent import triage_agent
    
    test_questions = [
        "求解 x + 5 = 10",
        "谁是美国第一任总统？",
        "今天天气怎么样？",
        "我是大一学生",
        "总结对话"
    ]
    
    print("=" * 50)
    print("测试 Triage Agent")
    print("=" * 50)
    
    for question in test_questions:
        result = await triage_agent.classify(question)
        print(f"\n问题: {question}")
        print(f"分类结果: {result}")


async def test_guardrail_agent():
    """测试 Guardrail Agent"""
    from agents.guardrail_agent import guardrail_agent
    
    test_questions = [
        "求解 x + 5 = 10",
        "帮我写个Python程序",
        "去日本旅游推荐哪里？"
    ]
    
    print("\n" + "=" * 50)
    print("测试 Guardrail Agent")
    print("=" * 50)
    
    for question in test_questions:
        should_reject, message = await guardrail_agent.check(question)
        print(f"\n问题: {question}")
        print(f"应该拒绝: {should_reject}")
        if should_reject:
            print(f"拒绝消息: {message}")


async def test_orchestrator():
    """测试 Agent 编排器"""
    from agents.orchestrator import orchestrator
    
    test_questions = [
        "求解 x + 5 = 10",
        "谁是美国第一任总统？",
        "今天天气怎么样？",
        "我是大一学生"
    ]
    
    print("\n" + "=" * 50)
    print("测试 Agent 编排器")
    print("=" * 50)
    
    for question in test_questions:
        result = await orchestrator.process_message(question)
        print(f"\n问题: {question}")
        print(f"回复: {result['response'][:100]}...")
        print(f"分类: {result.get('category')}")


def test_llm_client():
    """测试 LLM 客户端"""
    from agents.llm_client import llm_client
    
    print("\n" + "=" * 50)
    print("测试 LLM 客户端")
    print("=" * 50)
    
    result = llm_client.test_connection()
    print(f"提供商: {result.get('provider')}")
    print(f"模型: {llm_client.model_name}")
    print(f"连接状态: {'成功' if result.get('success') else '失败'}")
    print(f"消息: {result.get('message')}")


def test_config():
    """测试配置"""
    from app.config import ModelConfig
    
    print("\n" + "=" * 50)
    print("测试配置")
    print("=" * 50)
    
    print(f"当前提供商: {ModelConfig.get_active_provider()}")
    print(f"模型名称: {ModelConfig.get_model_name()}")
    print(f"OpenAI 配置: {ModelConfig.is_openai_configured()}")
    print(f"DeepSeek 配置: {ModelConfig.is_deepseek_configured()}")
    print(f"HKUST Azure 配置: {ModelConfig.is_hkust_azure_configured()}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("SmartTutor - Agent 系统测试")
    print("=" * 60)
    
    # 测试配置
    test_config()
    
    # 测试 LLM 客户端
    test_llm_client()
    
    # 测试各个 Agent
    await test_triage_agent()
    await test_guardrail_agent()
    await test_orchestrator()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
