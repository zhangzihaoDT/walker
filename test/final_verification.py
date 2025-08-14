#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证脚本 - 验证车型销量查询功能的完整实现
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from modules.sales_query_module import SalesQueryModule
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING)  # 减少日志输出

def test_key_scenarios():
    """测试关键场景"""
    print("🚀 开始最终验证测试")
    
    try:
        module = SalesQueryModule()
        
        # 加载数据
        data_path = "data/乘用车上险量_0723.parquet"
        if not os.path.exists(data_path):
            print(f"⚠️ 数据文件不存在: {data_path}")
            return False
            
        data = pd.read_parquet(data_path)
        print(f"✅ 数据加载成功，共 {len(data)} 条记录")
        
        # 关键测试场景
        test_cases = [
            {
                "name": "智己LS6车型查询",
                "question": "智己LS6 2024年销量",
                "expected_template": "车型销量查询"
            },
            {
                "name": "特斯拉Model Y车型查询", 
                "question": "特斯拉Model Y销量数据",
                "expected_template": "车型销量查询"
            },
            {
                "name": "品牌+车型组合查询",
                "question": "比亚迪汉销量",
                "expected_template": "车型销量查询"
            }
        ]
        
        success_count = 0
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n--- 测试 {i}: {case['name']} ---")
            print(f"问题: {case['question']}")
            
            try:
                result = module.run(data, {"user_question": case['question']})
                
                if result.get('success', False):
                    analysis = result.get('analysis', {})
                    template_used = analysis.get('template_used', '未知模板')
                    total_records = analysis.get('total_records', 0)
                    
                    print(f"✅ 查询成功")
                    print(f"使用模板: {template_used}")
                    print(f"记录数: {total_records}")
                    
                    # 检查模板选择
                    if case['expected_template'] in template_used:
                        print(f"✅ 模板选择正确")
                        success_count += 1
                    else:
                        print(f"⚠️ 模板选择不符合预期，期望: {case['expected_template']}, 实际: {template_used}")
                        
                    # 显示部分结果
                    data = result.get('data', [])
                    if data and len(data) > 0:
                        first_record = data[0]
                        print(f"示例结果: {first_record}")
                    else:
                        print(f"⚠️ 查询成功但无数据返回")
                        
                else:
                    error_info = result.get('analysis', {}).get('error') or result.get('error', '未知错误')
                    print(f"❌ 查询失败: {error_info}")
                    
            except Exception as e:
                print(f"❌ 测试异常: {str(e)}")
        
        print(f"\n📊 最终验证结果")
        print(f"成功: {success_count}/{len(test_cases)}")
        print(f"成功率: {success_count/len(test_cases)*100:.1f}%")
        
        if success_count == len(test_cases):
            print("\n🎉 所有关键功能验证通过！")
            print("\n✨ 实现的功能:")
            print("  • ✅ 新增车型销量查询模板")
            print("  • ✅ 优化模板选择逻辑（车型优先级最高）")
            print("  • ✅ 增强现有模板的多维度支持")
            print("  • ✅ 支持品牌+车型组合查询")
            return True
        else:
            print("\n⚠️ 部分功能需要进一步优化")
            return False
            
    except Exception as e:
        print(f"❌ 验证测试失败: {e}")
        return False

if __name__ == "__main__":
    test_key_scenarios()