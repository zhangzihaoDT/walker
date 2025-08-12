#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 DataDescribeModule 的字段读取能力
"""

import sys
sys.path.append('.')

from modules.data_describe_module import DataDescribeModule
import json

def test_field_reading():
    """测试字段读取功能"""
    print("🧪 测试 DataDescribeModule 字段读取能力")
    print("=" * 50)
    
    # 创建模块实例
    module = DataDescribeModule()
    
    # 测试参数
    params = {
        'data_source': 'data',  # 使用 data 目录
        'include_visualization': True
    }
    
    try:
        # 执行分析
        print("📊 开始分析数据...")
        results = module.execute(params)
        
        if results['success']:
            print("✅ 分析成功！")
            print(f"📋 模块: {results['module']}")
            
            # 显示字段信息
            if 'field_info' in results:
                field_info = results['field_info']
                print(f"\n🔍 字段信息:")
                print(f"  总字段数: {field_info.get('total_fields', 0)}")
                print(f"  数值字段: {len(field_info.get('numeric_fields', []))} 个")
                print(f"  文本字段: {len(field_info.get('text_fields', []))} 个")
                print(f"  日期字段: {len(field_info.get('datetime_fields', []))} 个")
                
                # 显示具体字段名称
                if field_info.get('numeric_fields'):
                    print(f"\n📊 数值字段列表:")
                    for field in field_info['numeric_fields'][:10]:  # 显示前10个
                        print(f"    - {field}")
                
                if field_info.get('text_fields'):
                    print(f"\n📝 文本字段列表:")
                    for field in field_info['text_fields'][:10]:  # 显示前10个
                        print(f"    - {field}")
                        
                # 显示字段详细信息示例
                if field_info.get('field_details'):
                    print(f"\n📋 字段详细信息示例 (前5个字段):")
                    field_details = field_info['field_details']
                    for i, (field_name, details) in enumerate(list(field_details.items())[:5]):
                        print(f"  {i+1}. {field_name}:")
                        print(f"     类型: {details.get('type', 'unknown')}")
                        print(f"     非空值: {details.get('non_null_count', 0)}")
                        print(f"     缺失值: {details.get('null_count', 0)}")
                        print(f"     唯一值: {details.get('unique_count', 0)}")
            else:
                print("\n⚠️  未找到字段信息")
            
            # 显示可用字段列表
            if 'available_fields' in results:
                available_fields = results['available_fields']
                print(f"\n🎯 可用字段总览 (共 {len(available_fields)} 个):")
                for i, field in enumerate(available_fields[:15], 1):  # 显示前15个
                    print(f"  {i:2d}. {field}")
                if len(available_fields) > 15:
                    print(f"     ... 还有 {len(available_fields) - 15} 个字段")
            
            # 显示总结
            print(f"\n📄 分析总结:")
            print(results['summary'])
            
            # 测试模块信息
            print(f"\n🔧 模块信息:")
            module_info = module.get_module_info()
            print(f"  支持动态字段检测: {module_info.get('supports_any_fields', False)}")
            print(f"  字段检测方式: {module_info.get('field_detection', 'unknown')}")
            print(f"  检测到的字段数: {len(module_info.get('detected_fields', []))}")
            
            # 测试兼容性检查
            print(f"\n🔍 兼容性测试:")
            test_fields = ['Order Number', '是否试驾', 'Product Name', 'owner_age']
            compatibility = module.check_database_compatibility('csv', test_fields)
            print(f"  兼容性: {compatibility['compatible']}")
            print(f"  评分: {compatibility['score']:.2f}")
            print(f"  原因: {compatibility['reason']}")
            
        else:
            print(f"❌ 分析失败: {results.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_field_reading()