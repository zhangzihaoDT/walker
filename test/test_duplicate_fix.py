#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重复"查询结果："输出修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.sales_query_module import SalesQueryModule
from agents.module_executor import get_module_executor
import json

def test_duplicate_output_fix():
    """测试重复输出修复"""
    print("=== 测试重复输出修复 ===")
    
    try:
        # 加载模块配置
        config_file = project_root / "modules" / "analysis_config.json"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        sales_query_config = None
        for module in config['modules']:
            if module['module_id'] == 'sales_query':
                sales_query_config = module
                break
        
        if not sales_query_config:
            print("❌ 未找到sales_query模块配置")
            return False
        
        # 创建模块执行器
        module_executor = get_module_executor()
        
        # 测试查询
        test_question = "智己LS6 2024年的销量"
        print(f"\n测试问题: {test_question}")
        
        params = {
            "data_source": "data/乘用车上险量_0723.parquet",
            "user_question": test_question
        }
        
        result = module_executor.execute_module(
            module_id='sales_query',
            parameters=params,
            module_config=sales_query_config
        )
        
        if result.get('success', False):
            summary = result.get('summary', '')
            data = result.get('data', [])
            
            print("\n=== 模块返回的摘要 ===")
            print(summary)
            
            print("\n=== 检查重复输出 ===")
            # 检查是否有重复的"查询结果："
            query_result_count = summary.count("查询结果：")
            print(f"摘要中'查询结果：'出现次数: {query_result_count}")
            
            if query_result_count <= 1:
                print("✅ 重复输出问题已修复")
            else:
                print("❌ 仍存在重复输出问题")
            
            # 检查数据质量
            print(f"\n=== 数据质量检查 ===")
            print(f"返回记录数: {len(data)}")
            
            if data:
                # 检查是否有0销量记录
                zero_sales_count = sum(1 for record in data if record.get('total_sales', 0) == 0)
                print(f"0销量记录数: {zero_sales_count}")
                
                if zero_sales_count == 0:
                    print("✅ 0销量记录过滤成功")
                else:
                    print("❌ 仍存在0销量记录")
                
                # 显示前3条记录
                print("\n前3条记录:")
                for i, record in enumerate(data[:3], 1):
                    brand = record.get('brand', 'N/A')
                    model = record.get('model_name', 'N/A')
                    sales = record.get('total_sales', 0)
                    print(f"  {i}. {brand} {model}: {sales:,} 辆")
            
            return True
        else:
            error = result.get('error', '未知错误')
            print(f"❌ 查询失败: {error}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    success = test_duplicate_output_fix()
    if success:
        print("\n🎉 测试完成")
    else:
        print("\n💥 测试失败")