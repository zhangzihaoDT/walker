#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI洞察生成功能演示脚本

这个脚本演示了如何使用新增的AI洞察生成功能来分析销量数据。
"""

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import json
from modules.sales_query_module import SalesQueryModule

def demo_ai_insights():
    """演示AI洞察生成功能"""
    print("=== AI洞察生成功能演示 ===")
    print("这个演示展示了如何使用AI对销量数据进行深度分析\n")
    
    # 创建销量查询模块实例
    module = SalesQueryModule()
    
    # 创建示例销量数据
    sales_data = pd.DataFrame([
        {'brand': '特斯拉', 'sales_volume': 28000, 'province': '上海', 'city': '上海市', 'month': '2024-01'},
        {'brand': '比亚迪', 'sales_volume': 35000, 'province': '广东', 'city': '深圳市', 'month': '2024-01'},
        {'brand': '蔚来', 'sales_volume': 15000, 'province': '江苏', 'city': '南京市', 'month': '2024-01'},
        {'brand': '理想', 'sales_volume': 22000, 'province': '北京', 'city': '北京市', 'month': '2024-01'},
        {'brand': '小鹏', 'sales_volume': 18000, 'province': '广东', 'city': '广州市', 'month': '2024-01'},
        {'brand': '智己', 'sales_volume': 12000, 'province': '上海', 'city': '上海市', 'month': '2024-01'},
        {'brand': '极氪', 'sales_volume': 16000, 'province': '浙江', 'city': '杭州市', 'month': '2024-01'},
        {'brand': '问界', 'sales_volume': 20000, 'province': '四川', 'city': '成都市', 'month': '2024-01'}
    ])
    
    print("📊 示例销量数据：")
    print(sales_data.to_string(index=False))
    print(f"\n数据概览：共 {len(sales_data)} 个品牌，总销量 {sales_data['sales_volume'].sum():,} 辆")
    
    # 模拟查询模板信息
    template_info = {
        'name': '新能源汽车品牌销量分析',
        'description': '分析各新能源汽车品牌在不同地区的销量表现'
    }
    
    # 模拟查询参数
    query_params = {
        'start_date': '2024-01-01',
        'end_date': '2024-01-31',
        'brand': None,
        'province': None
    }
    
    print("\n🤖 正在调用AI生成深度洞察...")
    
    try:
        # 生成完整的分析结果
        result = module._format_results(sales_data, template_info, query_params)
        
        # 显示AI生成的洞察
        insights = result.get('insights', [])
        
        if insights:
            print(f"\n✅ AI成功生成了 {len(insights)} 个业务洞察：\n")
            
            for i, insight in enumerate(insights, 1):
                print(f"{'='*60}")
                print(f"洞察 {i}")
                print(f"{'='*60}")
                print(insight)
                print()
        else:
            print("\n⚠️  未能生成AI洞察，使用基础统计分析")
            
        # 显示其他分析结果
        print(f"\n📈 数据统计摘要：")
        analysis = result.get('analysis', {})
        for key, value in analysis.items():
            print(f"- {key}: {value}")
            
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 演示完成 ===")
    print("\n💡 AI洞察功能特点：")
    print("- 🎯 自动识别市场趋势和竞争格局")
    print("- 📊 基于真实数据生成专业分析")
    print("- 🌍 考虑地域分布和时间趋势")
    print("- 💼 提供可操作的业务建议")
    print("- 🔄 支持失败回退到基础统计")

if __name__ == "__main__":
    demo_ai_insights()