#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意图解析器测试文件

测试新的意图识别功能，包括query_only类型的识别和路由逻辑。
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

from agents.intent_parser import IntentParser, get_intent_parser
from core.graph_builder import GraphBuilder

def test_intent_parser():
    """
    测试意图解析器的基本功能
    """
    print("=== 测试意图解析器 ===")
    
    parser = IntentParser()
    
    test_cases = [
        {
            "question": "你有什么数据？",
            "expected_intent": "data_query",
            "description": "数据概览查询"
        },
        {
            "question": "查询用户表中年龄大于25的记录",
            "expected_intent": "query_only",
            "description": "直接SQL查询"
        },
        {
            "question": "分析销售数据的趋势",
            "expected_intent": "data_analysis",
            "description": "数据分析请求"
        },
        {
            "question": "你好，今天天气怎么样？",
            "expected_intent": "general_chat",
            "description": "一般对话"
        },
        {
            "question": "筛选出价格大于100的商品",
            "expected_intent": "query_only",
            "description": "筛选查询"
        },
        {
            "question": "搜索包含关键词的记录",
            "expected_intent": "query_only",
            "description": "搜索查询"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['description']}")
        print(f"问题: {case['question']}")
        
        result = parser.parse_intent(case['question'])
        
        print(f"识别结果: {result}")
        print(f"期望意图: {case['expected_intent']}")
        print(f"实际意图: {result.get('intent')}")
        
        if result.get('intent') == case['expected_intent']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")

def test_graph_builder_routing():
    """
    测试图构建器的路由逻辑
    """
    print("\n=== 测试图构建器路由逻辑 ===")
    
    builder = GraphBuilder()
    
    test_states = [
        {
            "intent_result": {
                "intent": "query_only",
                "confidence": 0.9,
                "need_data_analysis": False
            },
            "expected_route": "sql_agent",
            "description": "直接查询路由"
        },
        {
            "intent_result": {
                "intent": "data_query",
                "confidence": 0.8,
                "need_data_analysis": True
            },
            "expected_route": "walker_strategy",
            "description": "Walker策略路由"
        },
        {
            "intent_result": {
                "intent": "data_analysis",
                "confidence": 0.9,
                "need_data_analysis": True
            },
            "expected_route": "walker_strategy",
            "description": "数据分析路由"
        },
        {
            "intent_result": {
                "intent": "general_chat",
                "confidence": 0.7,
                "need_data_analysis": False
            },
            "expected_route": "response_generation",
            "description": "一般对话路由"
        }
    ]
    
    for i, case in enumerate(test_states, 1):
        print(f"\n路由测试 {i}: {case['description']}")
        
        # 创建模拟状态
        state = {
            "user_question": "测试问题",
            "intent_result": case["intent_result"]
        }
        
        # 测试路由逻辑
        route = builder.should_use_walker(state)
        
        print(f"意图: {case['intent_result']['intent']}")
        print(f"期望路由: {case['expected_route']}")
        print(f"实际路由: {route}")
        
        if route == case['expected_route']:
            print("✅ 路由测试通过")
        else:
            print("❌ 路由测试失败")

def test_intent_node_integration():
    """
    测试意图识别节点的集成功能
    """
    print("\n=== 测试意图识别节点集成 ===")
    
    parser = get_intent_parser()
    
    test_questions = [
        "查询销售表中金额大于1000的记录",
        "分析用户行为数据",
        "你好，请问可以帮我什么？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n集成测试 {i}")
        print(f"问题: {question}")
        
        # 创建初始状态
        state = {
            "user_question": question,
            "intent_result": {},
            "analysis_result": "",
            "analysis_success": False,
            "final_response": "",
            "error_message": "",
            "walker_strategy": {},
            "execution_plan": [],
            "execution_results": []
        }
        
        # 执行意图识别节点
        updated_state = parser.create_intent_node(state)
        
        print(f"识别结果: {updated_state['intent_result']}")
        
        if 'error_message' in updated_state and updated_state['error_message']:
            print(f"❌ 出现错误: {updated_state['error_message']}")
        else:
            print("✅ 节点执行成功")

def main():
    """
    运行所有测试
    """
    print("开始测试意图解析器功能...\n")
    
    try:
        test_intent_parser()
        test_graph_builder_routing()
        test_intent_node_integration()
        
        print("\n=== 测试完成 ===")
        print("所有测试已执行完毕，请检查上述结果。")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()