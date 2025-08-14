#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试智己LS6查询问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.sales_query_module import SalesQueryModule
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_zhiji_query():
    """测试智己LS6查询"""
    print("=== 调试智己LS6查询问题 ===")
    
    try:
        # 初始化模块
        module = SalesQueryModule()
        
        # 测试问题
        test_question = "智己LS6 2024年的销量如何？"
        print(f"测试问题: {test_question}")
        
        # 准备参数
        params = {
            'user_question': test_question,
            'data_source': 'data/乘用车上险量_0723.parquet'
        }
        
        print("\n1. 准备数据...")
        data = module.prepare_data(None, params)
        print(f"数据加载成功，形状: {data.shape}")
        
        print("\n2. 提取查询参数...")
        extracted_params = module._extract_query_parameters(params)
        print(f"提取的参数: {extracted_params}")
        
        print("\n3. 选择查询模板...")
        template_info = module._select_template(extracted_params)
        print(f"选择的模板: {template_info['name']}")
        
        print("\n4. 执行查询...")
        result_df = module._execute_query(data, template_info, extracted_params)
        print(f"查询结果形状: {result_df.shape}")
        
        print("\n5. 格式化结果...")
        formatted_result = module._format_results(result_df, template_info, extracted_params)
        print(f"格式化结果: {type(formatted_result)}")
        
        print("\n6. 生成摘要...")
        summary = module.summarize(formatted_result)
        print(f"摘要: {summary[:200]}...")
        
        print("\n✅ 测试完成，未发现错误")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 详细分析错误
        error_str = str(e)
        if "sequence item 0: expected str instance, NoneType found" in error_str:
            print("\n🔍 发现None值错误，分析参数:")
            try:
                extracted_params = module._extract_query_parameters(params)
                for key, value in extracted_params.items():
                    if value is None:
                        print(f"  - {key}: None (可能导致错误)")
                    elif isinstance(value, list) and None in value:
                        print(f"  - {key}: {value} (包含None值)")
                    else:
                        print(f"  - {key}: {value}")
            except Exception as inner_e:
                print(f"参数提取也失败: {inner_e}")

if __name__ == "__main__":
    test_zhiji_query()