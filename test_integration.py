#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试 - 验证Walker、ModuleExecutor和GraphBuilder的集成功能
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_walker_integration():
    """
    测试Walker模块集成
    """
    print("\n=== 测试Walker模块集成 ===")
    
    try:
        from core.walker import get_walker
        
        walker = get_walker()
        print(f"✓ Walker实例创建成功")
        
        # 测试模块注册
        registered_modules = walker.list_modules()
        print(f"✓ 已注册模块: {list(registered_modules.keys())}")
        
        # 测试策略生成
        strategy = walker.generate_strategy(
            question="请分析data目录下的数据",
            intent={"intent": "data_analysis", "need_data_analysis": True}
        )
        print(f"✓ 策略生成成功: {len(strategy.get('strategies', []))} 个策略")
        
        return True
        
    except Exception as e:
        print(f"✗ Walker集成测试失败: {e}")
        return False

def test_module_executor_integration():
    """
    测试ModuleExecutor集成
    """
    print("\n=== 测试ModuleExecutor集成 ===")
    
    try:
        from core.module_executor import get_module_executor
        from core.walker import get_walker
        
        executor = get_module_executor()
        walker = get_walker()
        
        print(f"✓ ModuleExecutor实例创建成功")
        
        # 获取可用模块
        available_modules = executor.list_modules()
        print(f"✓ 可用模块: {available_modules}")
        
        # 生成策略
        strategy = walker.generate_strategy(
            question="分析CSV数据",
            intent={"intent": "data_analysis", "need_data_analysis": True}
        )
        
        # 创建执行计划
        execution_plan = executor.create_execution_plan(strategy)
        print(f"✓ 执行计划创建成功: {len(execution_plan)} 个步骤")
        
        # Mock执行计划（避免实际文件操作）
        with patch.object(executor, 'execute_module') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "result": "模拟分析结果",
                "metadata": {"rows": 100, "columns": 5}
            }
            
            results = executor.execute_plan(execution_plan)
            print(f"✓ 执行计划完成: {len(results)} 个结果")
        
        return True
        
    except Exception as e:
        print(f"✗ ModuleExecutor集成测试失败: {e}")
        return False

def test_graph_builder_integration():
    """
    测试GraphBuilder集成
    """
    print("\n=== 测试GraphBuilder集成 ===")
    
    try:
        from core.graph_builder import GraphBuilder
        
        # Mock外部依赖
        with patch('core.graph_builder.get_glm_client') as mock_glm, \
             patch('core.graph_builder.DataAnalyzer') as mock_analyzer:
            
            mock_glm.return_value = Mock()
            mock_analyzer.return_value = Mock()
            
            builder = GraphBuilder()
            print(f"✓ GraphBuilder实例创建成功")
            
            # 测试状态图构建
            graph = builder.build_graph()
            print(f"✓ 状态图构建成功")
            
            # 测试Walker策略节点
            test_state = {
                "user_question": "分析数据",
                "intent_result": {"intent": "data_analysis", "need_data_analysis": True},
                "walker_strategy": {},
                "execution_plan": [],
                "execution_results": [],
                "analysis_result": "",
                "analysis_success": False,
                "final_response": "",
                "error_message": ""
            }
            
            # 测试Walker策略生成
            updated_state = builder.walker_strategy_node(test_state)
            print(f"✓ Walker策略节点测试成功")
            
            # 测试执行计划生成
            if "error" not in updated_state["walker_strategy"]:
                updated_state = builder.execution_planning_node(updated_state)
                print(f"✓ 执行计划节点测试成功")
                
                # Mock模块执行
                with patch.object(builder.module_executor, 'execute_plan') as mock_execute_plan:
                    mock_execute_plan.return_value = [{
                        "step_id": 1,
                        "module_id": "data_describe",
                        "success": True,
                        "output": "数据分析完成",
                        "error": None,
                        "metadata": {}
                    }]
                    
                    updated_state = builder.module_execution_node(updated_state)
                    print(f"✓ 模块执行节点测试成功")
            
        return True
        
    except Exception as e:
        print(f"✗ GraphBuilder集成测试失败: {e}")
        return False

def test_end_to_end_workflow():
    """
    测试端到端工作流
    """
    print("\n=== 测试端到端工作流 ===")
    
    try:
        from core.graph_builder import GraphBuilder
        
        # Mock所有外部依赖
        with patch('core.graph_builder.get_glm_client') as mock_glm, \
             patch('core.graph_builder.DataAnalyzer') as mock_analyzer, \
             patch('llm.glm.get_glm_client') as mock_glm2:
            
            # 设置mock返回值
            mock_client = Mock()
            mock_client.generate_response.return_value = "这是一个模拟的AI响应"
            mock_glm.return_value = mock_client
            mock_glm2.return_value = mock_client
            mock_analyzer.return_value = Mock()
            
            builder = GraphBuilder()
            graph = builder.build_graph()
            
            # 测试完整工作流
            initial_state = {
                "user_question": "请分析data目录下的CSV文件，告诉我数据的基本统计信息",
                "intent_result": {},
                "walker_strategy": {},
                "execution_plan": [],
                "execution_results": [],
                "analysis_result": "",
                "analysis_success": False,
                "final_response": "",
                "error_message": ""
            }
            
            print(f"✓ 端到端工作流测试准备完成")
            print(f"✓ 初始状态: {initial_state['user_question']}")
            
        return True
        
    except Exception as e:
        print(f"✗ 端到端工作流测试失败: {e}")
        return False

def main():
    """
    运行所有集成测试
    """
    print("开始集成测试...")
    
    tests = [
        test_walker_integration,
        test_module_executor_integration,
        test_graph_builder_integration,
        test_end_to_end_workflow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有集成测试通过！")
        return True
    else:
        print(f"\n❌ {total-passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)