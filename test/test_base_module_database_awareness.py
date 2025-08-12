#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 BaseAnalysisModule 的数据库感知能力
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.base_module import BaseAnalysisModule
from typing import Dict, Any, List


class TestAnalysisModule(BaseAnalysisModule):
    """测试用的分析模块"""
    
    module_id = "test_module"
    module_name = "测试分析模块"
    description = "用于测试数据库感知能力的模块"
    
    # 数据库感知配置
    supported_databases = ['duckdb', 'csv']
    required_fields = ['id', 'name', 'value']
    optional_fields = ['category', 'timestamp']
    
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> Any:
        """准备测试数据"""
        return {"test_data": "prepared"}
    
    def run(self, data: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试分析"""
        return {
            "data": [{"result": "test"}],
            "analysis": {"count": 1},
            "visualization": {"type": "bar"},
            "insights": ["测试洞察"]
        }
    
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成测试总结"""
        return "这是一个测试分析的总结"


def test_database_compatibility():
    """测试数据库兼容性检查"""
    module = TestAnalysisModule()
    
    print("=== 测试数据库兼容性检查 ===")
    
    # 测试支持的数据库类型
    result1 = module.check_database_compatibility('duckdb', ['id', 'name', 'value', 'category'])
    print(f"DuckDB 兼容性: {result1}")
    assert result1['compatible'] == True
    assert result1['score'] > 0.5
    
    # 测试不支持的数据库类型
    result2 = module.check_database_compatibility('mysql', ['id', 'name', 'value'])
    print(f"MySQL 兼容性: {result2}")
    assert result2['compatible'] == False
    assert result2['score'] == 0.0
    
    # 测试缺少必需字段
    result3 = module.check_database_compatibility('csv', ['id', 'name'])  # 缺少 'value'
    print(f"缺少字段的兼容性: {result3}")
    assert result3['compatible'] == False
    assert 'value' in result3['missing_fields']
    
    print("✅ 数据库兼容性检查测试通过")


def test_data_requirements():
    """测试数据需求获取"""
    module = TestAnalysisModule()
    
    print("\n=== 测试数据需求获取 ===")
    
    requirements = module.get_data_requirements()
    print(f"数据需求: {requirements}")
    
    assert requirements['supported_databases'] == ['duckdb', 'csv']
    assert requirements['required_fields'] == ['id', 'name', 'value']
    assert requirements['optional_fields'] == ['category', 'timestamp']
    
    print("✅ 数据需求获取测试通过")


def test_module_info():
    """测试模块信息获取"""
    module = TestAnalysisModule()
    
    print("\n=== 测试模块信息获取 ===")
    
    info = module.get_module_info()
    print(f"模块信息: {info}")
    
    assert info['module_id'] == 'test_module'
    assert info['supported_databases'] == ['duckdb', 'csv']
    assert info['required_fields'] == ['id', 'name', 'value']
    assert info['optional_fields'] == ['category', 'timestamp']
    
    print("✅ 模块信息获取测试通过")


def test_execute_compatibility():
    """测试执行方法的兼容性"""
    module = TestAnalysisModule()
    
    print("\n=== 测试执行方法兼容性 ===")
    
    # 模拟数据上下文
    data_context = {
        'db_connector': None,  # 模拟连接器
        'table_name': 'test_table'
    }
    
    parameters = {'test_param': 'test_value'}
    
    result = module.execute(parameters, data_context)
    print(f"执行结果: {result}")
    
    assert result['success'] == True
    assert result['module'] == '测试分析模块'
    assert result['summary'] == '这是一个测试分析的总结'
    
    print("✅ 执行方法兼容性测试通过")


def main():
    """主测试函数"""
    print("开始测试 BaseAnalysisModule 数据库感知能力...\n")
    
    try:
        test_database_compatibility()
        test_data_requirements()
        test_module_info()
        test_execute_compatibility()
        
        print("\n🎉 所有测试通过！数据库感知能力工作正常。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    main()