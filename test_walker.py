#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walker模块测试脚本

测试Walker的核心功能：
1. 模块自动发现和注册
2. 策略生成
3. 策略执行
4. 结果聚合
5. 后续策略生成
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.walker import Walker, ModuleStrategy, get_walker


def test_walker_initialization():
    """测试Walker初始化"""
    print("\n=== 测试Walker初始化 ===")
    
    walker = Walker()
    status = walker.get_walker_status()
    
    print(f"✓ Walker初始化成功")
    print(f"  - 模块配置路径: {status['modules_config_path']}")
    print(f"  - 已注册模块数量: {status['registered_modules_count']}")
    print(f"  - 可用数据库数量: {status['available_databases_count']}")
    
    return walker


def test_module_auto_discovery(walker):
    """测试模块自动发现"""
    print("\n=== 测试模块自动发现 ===")
    
    try:
        walker.auto_discover_modules()
        
        registered_modules = walker.get_registered_modules_info()
        print(f"✓ 自动发现并注册了 {len(registered_modules)} 个模块")
        
        for module_id, module_info in registered_modules.items():
            print(f"  - {module_id}: {module_info['module_name']}")
            print(f"    支持数据库: {module_info['supported_databases']}")
            print(f"    必需字段: {module_info['required_fields']}")
        
        return len(registered_modules) > 0
        
    except Exception as e:
        print(f"✗ 模块自动发现失败: {e}")
        return False


def test_database_setup(walker):
    """测试数据库设置"""
    print("\n=== 测试数据库设置 ===")
    
    # 模拟数据库信息
    mock_databases = [
        {
            "type": "csv",
            "path": "/Users/zihao_/Documents/github/W33_utils_3/test_data.csv",
            "fields": ["id", "name", "age", "salary"],
            "size": 1000,
            "connector": None
        },
        {
            "type": "duckdb",
            "path": "/Users/zihao_/Documents/github/W33_utils_3/test_data.duckdb",
            "table_name": "employees",
            "fields": ["employee_id", "department", "salary", "hire_date"],
            "size": 5000,
            "connector": Mock()
        }
    ]
    
    walker.set_available_databases(mock_databases)
    
    status = walker.get_walker_status()
    print(f"✓ 设置了 {status['available_databases_count']} 个数据库")
    print(f"  - 数据库类型: {status['available_database_types']}")
    
    return True


def test_strategy_generation(walker):
    """测试策略生成"""
    print("\n=== 测试策略生成 ===")
    
    # 模拟用户意图
    user_intent = {
        "action": "analyze",
        "target": "data_description",
        "parameters": {
            "include_visualization": True
        },
        "data_source": "test_data.csv",
        "preferences": {
            "detail_level": "comprehensive"
        }
    }
    
    try:
        strategies = walker.generate_strategies(
            user_intent, 
            max_strategies=3,
            min_compatibility_score=0.3
        )
        
        print(f"✓ 生成了 {len(strategies)} 个策略")
        
        for i, strategy in enumerate(strategies, 1):
            print(f"  策略 {i}:")
            print(f"    - 模块: {strategy.module_name}")
            print(f"    - 兼容性分数: {strategy.compatibility_score:.2f}")
            print(f"    - 优先级: {strategy.priority}")
            print(f"    - 预估执行时间: {strategy.estimated_execution_time:.2f}s")
            print(f"    - 数据库类型: {strategy.database_info['type']}")
            print(f"    - 参数: {strategy.parameters}")
        
        return strategies
        
    except Exception as e:
        print(f"✗ 策略生成失败: {e}")
        return []


def test_strategy_execution(walker, strategies):
    """测试策略执行"""
    print("\n=== 测试策略执行 ===")
    
    if not strategies:
        print("⚠ 没有可执行的策略")
        return []
    
    # 选择第一个策略进行测试
    strategy = strategies[0]
    
    # Mock数据以避免实际文件操作
    with patch('modules.data_describe_module.DataAnalyzer') as mock_analyzer_class:
        # 创建mock analyzer实例
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock数据读取方法
        import pandas as pd
        mock_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 28, 32],
            'salary': [50000, 60000, 70000, 55000, 65000]
        })
        
        mock_analyzer.read_csv_file.return_value = mock_df
        mock_analyzer.describe_dataframe.return_value = {
            '数据集名称': 'test_data.csv',
            '数据形状': (5, 4),
            '行数': 5,
            '列数': 4,
            '列名': ['id', 'name', 'age', 'salary'],
            '数据类型': {'id': 'int64', 'name': 'object', 'age': 'int64', 'salary': 'int64'},
            '缺失值统计': {'id': 0, 'name': 0, 'age': 0, 'salary': 0},
            '内存使用': '0.16 MB',
            '数值列描述统计': {
                'id': {'mean': 3.0, 'std': 1.58, 'min': 1.0, 'max': 5.0},
                'age': {'mean': 30.0, 'std': 4.08, 'min': 25.0, 'max': 35.0},
                'salary': {'mean': 60000.0, 'std': 8367.0, 'min': 50000.0, 'max': 70000.0}
            }
        }
        
        try:
            result = walker.execute_strategy(strategy)
            
            print(f"✓ 策略执行完成")
            print(f"  - 成功: {result.success}")
            print(f"  - 执行时间: {result.execution_time:.2f}s")
            
            if result.success:
                print(f"  - 洞察数量: {len(result.insights)}")
                if result.insights:
                    print("  - 主要洞察:")
                    for insight in result.insights[:3]:
                        print(f"    • {insight}")
                
                if 'summary' in result.result:
                    print(f"  - 总结: {result.result['summary'][:100]}...")
            else:
                print(f"  - 错误: {result.error_message}")
            
            return [result]
            
        except Exception as e:
            print(f"✗ 策略执行失败: {e}")
            return []


def test_result_aggregation(walker, execution_results):
    """测试结果聚合"""
    print("\n=== 测试结果聚合 ===")
    
    if not execution_results:
        print("⚠ 没有执行结果可聚合")
        return
    
    try:
        aggregated = walker.aggregate_results(execution_results)
        
        print(f"✓ 结果聚合完成")
        print(f"  - 总策略数: {aggregated['total_strategies']}")
        print(f"  - 成功策略数: {aggregated['successful_strategies']}")
        print(f"  - 失败策略数: {aggregated['failed_strategies']}")
        print(f"  - 总执行时间: {aggregated['total_execution_time']:.2f}s")
        print(f"  - 聚合洞察数量: {len(aggregated['aggregated_insights'])}")
        
        if aggregated['summary']:
            print(f"  - 聚合总结: {aggregated['summary'][:150]}...")
        
        return aggregated
        
    except Exception as e:
        print(f"✗ 结果聚合失败: {e}")
        return None


def test_followup_generation(walker, execution_results):
    """测试后续策略生成"""
    print("\n=== 测试后续策略生成 ===")
    
    if not execution_results:
        print("⚠ 没有执行结果，无法生成后续策略")
        return
    
    try:
        followup_strategies = walker.generate_followup_strategies(execution_results)
        
        print(f"✓ 生成了 {len(followup_strategies)} 个后续策略")
        
        for i, strategy in enumerate(followup_strategies, 1):
            print(f"  后续策略 {i}:")
            print(f"    - 模块: {strategy.module_name}")
            print(f"    - 优先级: {strategy.priority}")
            print(f"    - 参数: {strategy.parameters}")
        
        return followup_strategies
        
    except Exception as e:
        print(f"✗ 后续策略生成失败: {e}")
        return []


def test_global_walker():
    """测试全局Walker实例"""
    print("\n=== 测试全局Walker实例 ===")
    
    try:
        walker1 = get_walker()
        walker2 = get_walker()
        
        # 应该是同一个实例
        assert walker1 is walker2, "全局Walker实例不一致"
        
        print("✓ 全局Walker实例测试通过")
        print(f"  - 实例ID: {id(walker1)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 全局Walker实例测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始Walker模块测试")
    
    try:
        # 1. 初始化测试
        walker = test_walker_initialization()
        
        # 2. 模块发现测试
        modules_discovered = test_module_auto_discovery(walker)
        
        if not modules_discovered:
            print("⚠ 跳过后续测试，因为没有发现模块")
            return
        
        # 3. 数据库设置测试
        test_database_setup(walker)
        
        # 4. 策略生成测试
        strategies = test_strategy_generation(walker)
        
        # 5. 策略执行测试
        execution_results = test_strategy_execution(walker, strategies)
        
        # 6. 结果聚合测试
        aggregated_result = test_result_aggregation(walker, execution_results)
        
        # 7. 后续策略生成测试
        followup_strategies = test_followup_generation(walker, execution_results)
        
        # 8. 全局实例测试
        test_global_walker()
        
        print("\n🎉 Walker模块测试完成！")
        
        # 显示执行历史
        history = walker.get_execution_history()
        print(f"\n📊 执行历史: {len(history)} 条记录")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()