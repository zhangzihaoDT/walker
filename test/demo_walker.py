#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walker模块演示脚本

展示Walker模块如何根据用户意图生成策略并执行分析任务。
"""

import sys
from pathlib import Path
from unittest.mock import patch, Mock

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_walker_basic_usage():
    """
    演示Walker的基本使用
    """
    print("\n=== Walker模块基本使用演示 ===")
    
    from core.walker import get_walker
    
    # 获取Walker实例
    walker = get_walker()
    print(f"✓ Walker实例创建成功")
    
    # 查看已注册的模块
    modules = walker.list_modules()
    print(f"✓ 已注册模块: {list(modules.keys())}")
    
    # 查看可用数据库
    databases = walker.get_available_databases()
    print(f"✓ 可用数据库: {databases}")
    
    return walker

def demo_strategy_generation(walker):
    """
    演示策略生成
    """
    print("\n=== 策略生成演示 ===")
    
    # 测试不同类型的用户意图
    test_cases = [
        {
            "question": "请分析data目录下的CSV文件",
            "intent": {"intent": "data_analysis", "need_data_analysis": True}
        },
        {
            "question": "查询销售数据的统计信息",
            "intent": {"intent": "data_query", "need_data_analysis": True}
        },
        {
            "question": "你好，今天天气怎么样？",
            "intent": {"intent": "general_chat", "need_data_analysis": False}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i} ---")
        print(f"问题: {case['question']}")
        print(f"意图: {case['intent']}")
        
        strategy = walker.generate_strategy(
            question=case['question'],
            intent=case['intent']
        )
        
        print(f"生成策略数量: {len(strategy.get('strategies', []))}")
        print(f"推理过程: {strategy.get('reasoning')}")
        print(f"置信度: {strategy.get('confidence')}")
        
        if strategy.get('strategies'):
            for j, strat in enumerate(strategy['strategies']):
                print(f"  策略 {j+1}:")
                print(f"    模块ID: {strat.get('module_id')}")
                print(f"    参数: {strat.get('parameters')}")
                print(f"    数据库: {strat.get('database_info', {}).get('name')}")

def demo_module_executor_integration():
    """
    演示ModuleExecutor集成
    """
    print("\n=== ModuleExecutor集成演示 ===")
    
    from agents.module_executor import get_module_executor
    from core.walker import get_walker
    
    walker = get_walker()
    executor = get_module_executor()
    
    print(f"✓ ModuleExecutor可用模块: {executor.list_modules()}")
    
    # 生成策略
    strategy = walker.generate_strategy(
        question="分析数据文件",
        intent={"intent": "data_analysis", "need_data_analysis": True}
    )
    
    # 创建执行计划
    execution_plan = executor.create_execution_plan(strategy)
    print(f"✓ 执行计划创建成功: {len(execution_plan)} 个步骤")
    
    if execution_plan:
        print("执行计划详情:")
        for step in execution_plan:
            print(f"  步骤 {step['step_id']}: {step['module_id']}")
            print(f"    参数: {step['parameters']}")
            print(f"    优先级: {step['priority']}")

def demo_graph_builder_integration():
    """
    演示GraphBuilder集成
    """
    print("\n=== GraphBuilder集成演示 ===")
    
    from core.graph_builder import GraphBuilder
    
    # Mock外部依赖
    with patch('core.graph_builder.get_glm_client') as mock_glm, \
         patch('core.graph_builder.DataAnalyzer') as mock_analyzer:
        
        mock_glm.return_value = Mock()
        mock_analyzer.return_value = Mock()
        
        builder = GraphBuilder()
        print(f"✓ GraphBuilder实例创建成功")
        
        # 构建状态图
        graph = builder.build_graph()
        print(f"✓ 状态图构建成功")
        
        # 测试新的节点
        test_state = {
            "user_question": "分析销售数据",
            "intent_result": {"intent": "data_analysis", "need_data_analysis": True},
            "walker_strategy": {},
            "execution_plan": [],
            "execution_results": [],
            "analysis_result": "",
            "analysis_success": False,
            "final_response": "",
            "error_message": ""
        }
        
        # 测试Walker策略节点
        updated_state = builder.walker_strategy_node(test_state)
        print(f"✓ Walker策略节点执行成功")
        
        # 测试执行计划节点
        updated_state = builder.execution_planning_node(updated_state)
        print(f"✓ 执行计划节点执行成功")
        
        # Mock模块执行
        with patch.object(builder.module_executor, 'execute_plan') as mock_execute:
            mock_execute.return_value = [{
                "step_id": 1,
                "module_id": "data_describe",
                "success": True,
                "output": "数据分析完成：发现100行数据，5个字段",
                "error": None,
                "metadata": {"rows": 100, "columns": 5}
            }]
            
            updated_state = builder.module_execution_node(updated_state)
            print(f"✓ 模块执行节点执行成功")
            print(f"  分析结果: {updated_state.get('analysis_result')}")
            print(f"  执行成功: {updated_state.get('analysis_success')}")

def demo_configuration_management():
    """
    演示配置管理
    """
    print("\n=== 配置管理演示 ===")
    
    # 查看analysis_config.json
    config_path = Path("modules/analysis_config.json")
    if config_path.exists():
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✓ 配置文件存在: {config_path}")
        print(f"✓ 已配置模块数量: {len(config.get('modules', []))}")
        
        for module in config.get('modules', []):
            print(f"  模块: {module.get('module_id')}")
            print(f"    名称: {module.get('module_name')}")
            print(f"    描述: {module.get('description')}")
            print(f"    支持数据库: {module.get('supported_databases', [])}")
    else:
        print(f"✗ 配置文件不存在: {config_path}")

def main():
    """
    运行所有演示
    """
    print("🚀 Walker模块功能演示")
    print("=" * 50)
    
    try:
        # 基本使用演示
        walker = demo_walker_basic_usage()
        
        # 策略生成演示
        demo_strategy_generation(walker)
        
        # ModuleExecutor集成演示
        demo_module_executor_integration()
        
        # GraphBuilder集成演示
        demo_graph_builder_integration()
        
        # 配置管理演示
        demo_configuration_management()
        
        print("\n🎉 所有演示完成！")
        print("\n📝 总结:")
        print("1. ✓ Walker模块成功集成到系统中")
        print("2. ✓ 支持根据用户意图生成智能策略")
        print("3. ✓ ModuleExecutor能够执行策略计划")
        print("4. ✓ GraphBuilder集成了新的Walker流程")
        print("5. ✓ 配置管理系统正常工作")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)