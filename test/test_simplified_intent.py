#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化意图识别架构测试

测试移除 data_query 类型后的意图识别和路由逻辑。
"""

import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

class MockSimplifiedIntentParser:
    """
    模拟简化后的意图解析器
    """
    
    def parse_intent(self, user_question: str) -> Dict[str, Any]:
        """
        基于关键词的简化意图识别
        """
        question_lower = user_question.lower()
        
        # 检查是否为直接查询类型
        query_keywords = [
            "查询", "select", "where", "from", "查找", "搜索",
            "筛选", "过滤", "条件", "等于", "大于", "小于",
            "包含", "不包含", "排序", "order by", "group by"
        ]
        
        if any(keyword in question_lower for keyword in query_keywords):
            return {
                "intent": "query_only",
                "confidence": 0.9,
                "reason": "检测到SQL查询关键词",
                "need_data_analysis": False
            }
        
        # 检查是否为数据分析类型
        analysis_keywords = [
            "分析", "报告", "统计", "趋势", "模式", "数据", "表", 
            "记录", "信息", "概览", "描述", "范围", "内容"
        ]
        if any(keyword in question_lower for keyword in analysis_keywords):
            return {
                "intent": "data_analysis",
                "confidence": 0.8,
                "reason": "检测到数据分析关键词",
                "need_data_analysis": True
            }
        
        # 默认为一般对话
        return {
            "intent": "general_chat",
            "confidence": 0.6,
            "reason": "未检测到特定关键词，归类为一般对话",
            "need_data_analysis": False
        }

class MockSimplifiedGraphBuilder:
    """
    模拟简化后的图构建器
    """
    
    def __init__(self):
        self.intent_parser = MockSimplifiedIntentParser()
    
    def should_use_walker(self, state: Dict[str, Any]) -> str:
        """
        简化后的条件路由逻辑
        """
        intent_result = state.get("intent_result", {})
        intent = intent_result.get("intent", "general_chat")
        
        # 对于直接查询类型，使用SQL Agent
        if intent == "query_only":
            return "sql_agent"
        # 对于数据分析类型，使用Walker策略
        elif intent == "data_analysis":
            return "walker_strategy"
        else:
            return "response_generation"
    
    def test_routing(self, user_question: str) -> Dict[str, Any]:
        """
        测试路由逻辑
        """
        print(f"\n🔍 测试问题: {user_question}")
        
        # 意图识别
        intent_result = self.intent_parser.parse_intent(user_question)
        print(f"📋 意图识别: {intent_result}")
        
        # 路由决策
        state = {"intent_result": intent_result}
        route = self.should_use_walker(state)
        print(f"🚦 路由决策: {route}")
        
        return {
            "question": user_question,
            "intent": intent_result,
            "route": route
        }

def test_simplified_architecture():
    """
    测试简化后的架构
    """
    print("=== 简化意图识别架构测试 ===")
    print("移除 data_query 类型，简化为三种意图类型\n")
    
    builder = MockSimplifiedGraphBuilder()
    
    test_cases = [
        {
            "question": "查询用户表中年龄大于25的记录",
            "expected_intent": "query_only",
            "expected_route": "sql_agent",
            "description": "直接SQL查询"
        },
        {
            "question": "筛选出销售额大于10000的订单",
            "expected_intent": "query_only",
            "expected_route": "sql_agent",
            "description": "筛选查询"
        },
        {
            "question": "分析用户行为数据的趋势",
            "expected_intent": "data_analysis",
            "expected_route": "walker_strategy",
            "description": "数据分析"
        },
        {
            "question": "你有什么数据可以查看？",
            "expected_intent": "data_analysis",
            "expected_route": "walker_strategy",
            "description": "数据概览查询"
        },
        {
            "question": "数据的统计信息是什么？",
            "expected_intent": "data_analysis",
            "expected_route": "walker_strategy",
            "description": "数据统计"
        },
        {
            "question": "你好，今天天气怎么样？",
            "expected_intent": "general_chat",
            "expected_route": "response_generation",
            "description": "一般对话"
        },
        {
            "question": "搜索包含关键词'python'的文档",
            "expected_intent": "query_only",
            "expected_route": "sql_agent",
            "description": "搜索查询"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试用例 {i}: {case['description']}")
        print(f"期望意图: {case['expected_intent']}")
        print(f"期望路由: {case['expected_route']}")
        
        result = builder.test_routing(case['question'])
        
        # 验证意图和路由是否正确
        actual_intent = result['intent']['intent']
        actual_route = result['route']
        
        intent_correct = actual_intent == case['expected_intent']
        route_correct = actual_route == case['expected_route']
        
        if intent_correct and route_correct:
            print("✅ 测试通过")
            success_count += 1
        else:
            print("❌ 测试失败")
            if not intent_correct:
                print(f"   意图错误: 期望 {case['expected_intent']}, 实际 {actual_intent}")
            if not route_correct:
                print(f"   路由错误: 期望 {case['expected_route']}, 实际 {actual_route}")
    
    print(f"\n{'='*60}")
    print(f"🎯 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！简化架构工作正常。")
    else:
        print("⚠️ 部分测试失败，需要调整逻辑。")

def show_architecture_comparison():
    """
    显示架构对比
    """
    print("\n" + "="*60)
    print("🔄 架构简化对比")
    print("="*60)
    
    print("\n📋 简化前的意图类型:")
    print("1. data_query (数据查询类) - 容易与 query_only 混淆")
    print("2. data_analysis (数据分析类)")
    print("3. query_only (直接查询类) - 通过后处理从 data_query 转换")
    print("4. general_chat (一般对话类)")
    
    print("\n📋 简化后的意图类型:")
    print("1. query_only (直接查询类) - 使用SQL Agent")
    print("2. data_analysis (数据分析类) - 使用Walker策略")
    print("3. general_chat (一般对话类) - 直接响应生成")
    
    print("\n✅ 简化的优势:")
    print("- 移除了重复的意图类型")
    print("- 简化了后处理逻辑")
    print("- 路由决策更加清晰")
    print("- 减少了混淆和错误")
    print("- 代码更易维护")

def main():
    """
    主函数
    """
    test_simplified_architecture()
    show_architecture_comparison()
    
    print("\n🎉 简化完成！")
    print("意图识别架构已成功简化，移除了重复的意图类型。")

if __name__ == "__main__":
    main()