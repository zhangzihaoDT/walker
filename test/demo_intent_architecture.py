#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意图识别架构演示

演示新的意图识别架构，包括query_only分支和SQL Agent的工作流程。
不依赖外部API，使用模拟数据进行演示。
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

class MockIntentParser:
    """
    模拟意图解析器，不依赖外部API
    """
    
    def parse_intent(self, user_question: str) -> Dict[str, Any]:
        """
        基于关键词的简单意图识别
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
        analysis_keywords = ["分析", "报告", "统计", "趋势", "模式"]
        if any(keyword in question_lower for keyword in analysis_keywords):
            return {
                "intent": "data_analysis",
                "confidence": 0.8,
                "reason": "检测到数据分析关键词",
                "need_data_analysis": True
            }
        
        # 检查是否为数据查询类型
        data_keywords = ["数据", "表", "记录", "信息"]
        if any(keyword in question_lower for keyword in data_keywords):
            return {
                "intent": "data_query",
                "confidence": 0.7,
                "reason": "检测到数据查询关键词",
                "need_data_analysis": True
            }
        
        # 默认为一般对话
        return {
            "intent": "general_chat",
            "confidence": 0.6,
            "reason": "未检测到特定关键词，归类为一般对话",
            "need_data_analysis": False
        }

class MockGraphBuilder:
    """
    模拟图构建器，演示路由逻辑
    """
    
    def __init__(self):
        self.intent_parser = MockIntentParser()
    
    def should_use_walker(self, state: Dict[str, Any]) -> str:
        """
        条件路由：判断使用哪种处理策略
        """
        intent_result = state.get("intent_result", {})
        need_analysis = intent_result.get("need_data_analysis", False)
        intent = intent_result.get("intent", "general_chat")
        
        # 对于直接查询类型，使用SQL Agent
        if intent == "query_only":
            return "sql_agent"
        # 对于复杂的数据查询和分析，使用Walker策略
        elif need_analysis and intent in ["data_query", "data_analysis"]:
            return "walker_strategy"
        else:
            return "response_generation"
    
    def simulate_workflow(self, user_question: str) -> Dict[str, Any]:
        """
        模拟完整的工作流程
        """
        print(f"\n🔍 处理问题: {user_question}")
        
        # 步骤1: 意图识别
        intent_result = self.intent_parser.parse_intent(user_question)
        print(f"📋 意图识别结果: {intent_result}")
        
        # 步骤2: 路由决策
        state = {"intent_result": intent_result}
        route = self.should_use_walker(state)
        print(f"🚦 路由决策: {route}")
        
        # 步骤3: 模拟执行
        if route == "sql_agent":
            result = self._simulate_sql_agent(user_question)
        elif route == "walker_strategy":
            result = self._simulate_walker_strategy(user_question)
        else:
            result = self._simulate_response_generation(user_question)
        
        print(f"✅ 执行结果: {result}")
        return result
    
    def _simulate_sql_agent(self, question: str) -> str:
        """
        模拟SQL Agent执行
        """
        return f"SQL Agent执行: 针对'{question}'生成并执行了SQL查询，返回了相关数据记录。"
    
    def _simulate_walker_strategy(self, question: str) -> str:
        """
        模拟Walker策略执行
        """
        return f"Walker策略执行: 针对'{question}'制定了智能分析策略，调用了相关分析模块。"
    
    def _simulate_response_generation(self, question: str) -> str:
        """
        模拟响应生成
        """
        return f"直接响应生成: 针对'{question}'生成了友好的对话回复。"

def demo_architecture():
    """
    演示新架构的工作流程
    """
    print("=== 意图识别架构演示 ===")
    print("展示新的query_only分支和SQL Agent的工作流程\n")
    
    builder = MockGraphBuilder()
    
    test_cases = [
        {
            "question": "查询用户表中年龄大于25的记录",
            "expected_route": "sql_agent",
            "description": "直接SQL查询"
        },
        {
            "question": "筛选出销售额大于10000的订单",
            "expected_route": "sql_agent",
            "description": "筛选查询"
        },
        {
            "question": "分析用户行为数据的趋势",
            "expected_route": "walker_strategy",
            "description": "数据分析"
        },
        {
            "question": "你有什么数据可以查看？",
            "expected_route": "walker_strategy",
            "description": "数据概览查询"
        },
        {
            "question": "你好，今天天气怎么样？",
            "expected_route": "response_generation",
            "description": "一般对话"
        },
        {
            "question": "搜索包含关键词'python'的文档",
            "expected_route": "sql_agent",
            "description": "搜索查询"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试用例 {i}: {case['description']}")
        print(f"期望路由: {case['expected_route']}")
        
        result = builder.simulate_workflow(case['question'])
        
        # 验证路由是否正确
        state = {"intent_result": builder.intent_parser.parse_intent(case['question'])}
        actual_route = builder.should_use_walker(state)
        
        if actual_route == case['expected_route']:
            print("🎯 路由验证: ✅ 正确")
        else:
            print(f"🎯 路由验证: ❌ 错误 (期望: {case['expected_route']}, 实际: {actual_route})")

def show_architecture_summary():
    """
    显示架构变化总结
    """
    print("\n" + "="*60)
    print("🏗️  架构变化总结")
    print("="*60)
    
    changes = [
        "✅ 将意图识别逻辑独立到 agents/intent_parser.py",
        "✅ 新增 query_only 意图类型，专门处理直接SQL查询",
        "✅ 添加 SQL Agent 节点，替代传统数据分析分支",
        "✅ 更新 prompts.py 中的意图识别提示词",
        "✅ 修改 graph_builder.py 的路由逻辑",
        "✅ 更新意图识别流程图文档",
        "✅ 创建测试文件验证新功能"
    ]
    
    for change in changes:
        print(change)
    
    print("\n🔄 新的处理流程:")
    print("1. 用户输入 → 意图识别 (intent_parser.py)")
    print("2. 路由决策:")
    print("   - query_only → SQL Agent")
    print("   - data_query/data_analysis → Walker策略")
    print("   - general_chat → 直接响应生成")
    print("3. 执行相应的处理逻辑")
    print("4. 生成最终响应")

def main():
    """
    主函数
    """
    demo_architecture()
    show_architecture_summary()
    
    print("\n🎉 演示完成！")
    print("新的意图识别架构已成功实现，支持更精确的查询路由。")

if __name__ == "__main__":
    main()