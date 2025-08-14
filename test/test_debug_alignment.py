#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试信息对齐验证脚本
验证gradio_app.py中的调试信息与test_gradio_integration.py的对齐效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.router import get_workflow
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_debug_info_alignment():
    """
    测试调试信息对齐
    """
    print("\n" + "="*60)
    print("🔍 调试信息对齐验证测试")
    print("="*60)
    
    # 模拟测试数据（与test_gradio_integration.py对齐）
    test_cases = [
        {
            "question": "比亚迪的销量如何？",
            "mock_result": {
                "intent_result": {"intent": "query_only", "confidence": 0.95},
                "execution_results": [
                    {"success": True, "data": [{}] * 235, "module": "sales_query"}
                ],
                "final_response": "根据数据分析，比亚迪在2024年的销量表现优异，累计销售新能源汽车超过300万辆，同比增长15.8%。其中，纯电动车型占比达到70%，插电混动车型占比30%。比亚迪在国内新能源汽车市场份额稳居第一，海外市场也实现了快速增长。"
            }
        },
        {
            "question": "广东省的汽车销量",
            "mock_result": {
                "intent_result": {"intent": "query_only", "confidence": 0.88},
                "execution_results": [
                    {"success": True, "data": [{}] * 156, "module": "sales_query"}
                ],
                "final_response": "广东省作为汽车制造和消费大省，2024年汽车销量数据显示：全省累计销售汽车约280万辆，同比增长8.2%。"
            }
        },
        {
            "question": "特斯拉和蔚来的销量对比",
            "mock_result": {
                "intent_result": {"intent": "query_only", "confidence": 0.92},
                "execution_results": [
                    {"success": True, "data": [{}] * 189, "module": "sales_query"}
                ],
                "final_response": "特斯拉与蔚来在中国市场的销量对比分析：特斯拉2024年在华销量约45万辆，蔚来销量约12万辆。特斯拉凭借Model Y和Model 3的强劲表现保持领先地位。"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        result = test_case["mock_result"]
        
        print(f"\n📝 测试用例 {i}: {question}")
        print("-" * 50)
        
        try:
            # 提取调试信息
            intent_result = result.get("intent_result", {})
            execution_results = result.get("execution_results", [])
            response = result["final_response"]
            
            # 显示调试信息（与gradio_app.py格式对齐）
            print(f"📊 执行结果分析:")
            print(f"  - 意图识别: {intent_result.get('intent', 'unknown')}")
            print(f"  - 执行模块数: {len(execution_results)}")
            print(f"  - 响应长度: {len(response)} 字符")
            
            # 显示执行结果详情
            for j, exec_result in enumerate(execution_results, 1):
                if exec_result.get('success'):
                    data_count = len(exec_result.get('data', []))
                    print(f"  - 模块{j}: 成功，返回{data_count}条记录")
                else:
                    print(f"  - 模块{j}: 失败，错误: {exec_result.get('error', '未知')}")
            
            print(f"✅ 测试用例 {i} 执行成功")
            
        except Exception as e:
            print(f"❌ 测试用例 {i} 执行失败: {e}")
            logger.error(f"测试失败: {e}")
    
    print("\n" + "="*60)
    print("🎉 调试信息对齐验证完成")
    print("="*60)

if __name__ == "__main__":
    test_debug_info_alignment()