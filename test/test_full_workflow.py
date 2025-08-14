#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整工作流的重复输出修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.graph_builder import get_graph_builder

def test_full_workflow():
    """测试完整工作流"""
    print("=== 测试完整工作流重复输出修复 ===")
    
    try:
        # 获取图构建器
        graph_builder = get_graph_builder()
        
        # 测试查询
        test_question = "智己LS6 2024年的销量"
        print(f"\n测试问题: {test_question}")
        
        # 构建初始状态
        initial_state = {
            "user_question": test_question,
            "intent_result": {},
            "analysis_result": "",
            "analysis_success": False,
            "final_response": "",
            "error_message": "",
            "walker_strategy": {},
            "execution_plan": [],
            "execution_results": [],
            "sql_result": ""
        }
        
        # 执行意图识别
        print("\n1. 执行意图识别...")
        state = graph_builder.recognize_intent_node(initial_state)
        intent = state["intent_result"].get("intent", "unknown")
        print(f"识别的意图: {intent}")
        
        # 执行SQL代理节点
        if intent == "query_only":
            print("\n2. 执行SQL代理节点...")
            state = graph_builder.sql_agent_node(state)
            sql_result = state.get("sql_result", "")
            print(f"SQL结果长度: {len(sql_result)} 字符")
            
            # 检查SQL结果中的重复输出
            query_result_count = sql_result.count("查询结果：")
            print(f"SQL结果中'查询结果：'出现次数: {query_result_count}")
            
            # 执行响应生成
            print("\n3. 执行响应生成...")
            state = graph_builder.response_generation_node(state)
            final_response = state.get("final_response", "")
            
            print("\n=== 最终响应 ===")
            print(final_response)
            
            # 检查最终响应中的重复输出
            final_query_result_count = final_response.count("查询结果：")
            print(f"\n=== 重复输出检查 ===")
            print(f"最终响应中'查询结果：'出现次数: {final_query_result_count}")
            
            if final_query_result_count <= 1:
                print("✅ 完整工作流重复输出问题已修复")
                return True
            else:
                print("❌ 完整工作流仍存在重复输出问题")
                return False
        else:
            print(f"❌ 意图识别错误，期望query_only，实际{intent}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_workflow()
    if success:
        print("\n🎉 完整工作流测试成功")
    else:
        print("\n💥 完整工作流测试失败")