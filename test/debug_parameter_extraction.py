#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试参数提取功能
"""

import sys
sys.path.append('.')

from modules.sales_query_module import SalesQueryModule
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_parameter_extraction():
    """测试参数提取功能"""
    
    # 初始化模块
    module = SalesQueryModule()
    
    # 测试用例
    test_cases = [
        "智己LS6 2024年销量",
        "特斯拉Model Y销量数据",
        "比亚迪汉EV销量",
        "2024年智己LS6销量情况"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {question} ---")
        
        # 测试GLM参数提取
        try:
            params = {'user_question': question}
            extracted = module._extract_query_parameters(params)
            
            print(f"提取结果:")
            print(f"  brands: {extracted.get('brands', [])}")
            print(f"  model_names: {extracted.get('model_names', [])}")
            print(f"  start_date: {extracted.get('start_date')}")
            print(f"  end_date: {extracted.get('end_date')}")
            print(f"  time_granularity: {extracted.get('time_granularity')}")
            
            # 测试模板选择
            template = module._select_template(extracted)
            print(f"  选择模板: {template['name']}")
            
        except Exception as e:
            print(f"❌ 参数提取失败: {e}")
            
        # 测试备用方法
        try:
            fallback_extracted = module._extract_query_parameters_fallback(question)
            print(f"\n备用方法结果:")
            print(f"  brands: {fallback_extracted.get('brands', [])}")
            print(f"  model_names: {fallback_extracted.get('model_names', [])}")
            print(f"  start_date: {fallback_extracted.get('start_date')}")
            print(f"  end_date: {fallback_extracted.get('end_date')}")
            
        except Exception as e:
            print(f"❌ 备用方法失败: {e}")

if __name__ == "__main__":
    test_parameter_extraction()