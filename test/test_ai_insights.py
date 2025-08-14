#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI洞察生成功能
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sales_query_module import SalesQueryModule
import pandas as pd
import json

def test_ai_insights():
    """测试AI洞察生成功能"""
    print("=== 测试AI洞察生成功能 ===")
    
    try:
        # 直接测试GLM客户端
        from llm.glm import GLMClient
        from llm.prompts import AI_INSIGHTS_GENERATION_PROMPT
        
        print("\n正在初始化GLM客户端...")
        glm_client = GLMClient()
        
        # 创建测试数据
        test_data = pd.DataFrame([
            {'brand': '智己', 'sales_volume': 15000, 'province': '上海'},
            {'brand': '蔚来', 'sales_volume': 12000, 'province': '江苏'},
            {'brand': '理想', 'sales_volume': 18000, 'province': '北京'}
        ])
        
        # 准备数据摘要
        query_data = json.dumps({
            'total_rows': len(test_data),
            'columns': list(test_data.columns),
            'sample_data': test_data.to_dict('records'),
            'sales_summary': {
                'total': float(test_data['sales_volume'].sum()),
                'average': float(test_data['sales_volume'].mean()),
                'max': float(test_data['sales_volume'].max()),
                'min': float(test_data['sales_volume'].min())
            }
        }, ensure_ascii=False, indent=2)
        
        # 构建提示词
        prompt = AI_INSIGHTS_GENERATION_PROMPT.format(
            query_data=query_data,
            query_params="品牌: 智己, 蔚来, 理想; 地区: 上海, 江苏, 北京; 时间范围: 2024-01-01 - 2024-12-31",
            user_question="品牌销量查询"
        )
        
        print("\n正在调用GLM生成洞察...")
        raw_response = glm_client.generate_response(prompt)
        
        print("\n--- GLM原始响应 ---")
        print(raw_response)
        print("--- 响应结束 ---")
        
        # 尝试解析JSON
        try:
            import re
            
            def fix_json_format(json_str):
                """修复常见的JSON格式问题"""
                # 移除多余的空格和换行
                json_str = re.sub(r'\s+', ' ', json_str)
                # 确保字符串值被正确引用
                json_str = re.sub(r'([{,]\s*"[^"]+"\s*:\s*)([^"\[{][^,}\]]*)', r'\1"\2"', json_str)
                return json_str
            
            # 查找JSON数组
            json_match = re.search(r'\[.*?\]', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                print(f"\n原始JSON: {json_str[:200]}...")
                
                # 尝试修复JSON格式
                try:
                    insights_data = json.loads(json_str)
                except json.JSONDecodeError:
                    print("\n尝试修复JSON格式...")
                    fixed_json = fix_json_format(json_str)
                    print(f"修复后JSON: {fixed_json[:200]}...")
                    try:
                        insights_data = json.loads(fixed_json)
                    except json.JSONDecodeError:
                        # 如果还是失败，尝试手动解析
                        print("\n手动解析JSON内容...")
                        title_matches = re.findall(r'"title"\s*:\s*"([^"]+)"', json_str)
                        content_matches = re.findall(r'"content"\s*:\s*"([^"]+)"', json_str)
                        
                        insights_data = []
                        for i, title in enumerate(title_matches):
                            insight = {"title": title}
                            if i < len(content_matches):
                                insight["content"] = content_matches[i]
                            insights_data.append(insight)
                
                print(f"\n成功解析 {len(insights_data)} 个洞察：")
                for i, insight in enumerate(insights_data, 1):
                    print(f"{i}. 标题: {insight.get('title', 'N/A')}")
                    print(f"   内容: {insight.get('content', 'N/A')[:100]}...")
                    if insight.get('recommendation'):
                        print(f"   建议: {insight.get('recommendation')[:100]}...")
                    print()
            else:
                print("\n未找到JSON格式的响应")
                
        except Exception as parse_e:
            print(f"\nJSON解析失败: {parse_e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== AI洞察生成测试完成 ===")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_basic_insights_fallback():
    """测试基础洞察备选方案"""
    print("\n=== 测试基础洞察备选方案 ===")
    
    module = SalesQueryModule()
    
    # 创建测试数据
    test_data = pd.DataFrame([
        {'brand': '智己', 'sales_volume': 15000},
        {'brand': '蔚来', 'sales_volume': 12000},
        {'brand': '理想', 'sales_volume': 18000}
    ])
    
    template_info = {'name': '品牌销量查询'}
    params = {}
    
    try:
        # 直接测试基础洞察
        basic_insights = module._generate_basic_insights(test_data, template_info, params)
        
        print(f"\n基础洞察 ({len(basic_insights)} 个)：")
        for i, insight in enumerate(basic_insights, 1):
            print(f"{i}. {insight}")
            
    except Exception as e:
        print(f"基础洞察测试失败: {e}")

def test_data_preparation():
    """测试数据准备功能"""
    print("\n=== 测试数据准备功能 ===")
    
    module = SalesQueryModule()
    
    # 创建测试数据
    test_data = pd.DataFrame([
        {'brand': '智己', 'sales_volume': 15000, 'province': '上海'},
        {'brand': '蔚来', 'sales_volume': 12000, 'province': '江苏'},
        {'brand': '理想', 'sales_volume': 18000, 'province': '北京'}
    ])
    
    try:
        # 测试数据准备
        prepared_data = module._prepare_data_for_ai(test_data)
        print("\n准备的数据摘要：")
        print(prepared_data)
        
        # 测试品牌提取
        brands = module._extract_brands(test_data)
        print(f"\n提取的品牌: {brands}")
        
        # 测试地区提取
        regions = module._extract_regions(test_data)
        print(f"提取的地区: {regions}")
        
        # 测试时间范围提取
        params = {'start_date': '2024-01-01', 'end_date': '2024-12-31'}
        time_range = module._extract_time_range(params)
        print(f"提取的时间范围: {time_range}")
        
    except Exception as e:
        print(f"数据准备测试失败: {e}")

def test_full_integration():
    """测试完整的销量查询模块集成"""
    print("=== 测试完整集成功能 ===")
    
    try:
        # 创建销量查询模块实例
        module = SalesQueryModule()
        
        # 创建测试数据
        test_data = pd.DataFrame([
            {'brand': '智己', 'sales_volume': 15000, 'province': '上海', 'city': '上海市'},
            {'brand': '蔚来', 'sales_volume': 12000, 'province': '江苏', 'city': '南京市'},
            {'brand': '理想', 'sales_volume': 18000, 'province': '北京', 'city': '北京市'},
            {'brand': '小鹏', 'sales_volume': 14000, 'province': '广东', 'city': '广州市'},
            {'brand': '比亚迪', 'sales_volume': 25000, 'province': '广东', 'city': '深圳市'}
        ])
        
        # 模拟模板信息
        template_info = {
            'name': '品牌销量查询',
            'description': '查询各品牌的销量数据'
        }
        
        # 模拟查询参数
        params = {
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'brand': None,
            'province': None
        }
        
        print("\n正在生成完整的查询结果...")
        
        # 测试完整的结果格式化（包括AI洞察）
        result = module._format_results(test_data, template_info, params)
        
        print(f"\n查询结果包含以下部分：")
        for key in result.keys():
            print(f"- {key}")
        
        print(f"\n生成了 {len(result.get('insights', []))} 个洞察：")
        for i, insight in enumerate(result.get('insights', []), 1):
            print(f"{i}. {insight[:100]}...")
        
        print("\n=== 完整集成测试完成 ===")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行所有测试
    test_data_preparation()
    test_basic_insights_fallback()
    test_ai_insights()
    test_full_integration()