#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的意图识别逻辑
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.intent_parser import IntentParser

def test_intent_recognition():
    """测试意图识别修复"""
    print("🔍 测试修复后的意图识别逻辑")
    print("=" * 50)
    
    parser = IntentParser()
    
    test_cases = [
        "比亚迪2024年销量表现",
        "查看特斯拉的业绩数据",
        "分析苹果公司的销售趋势",
        "你好",
        "帮助"
    ]
    
    for question in test_cases:
        print(f"\n📝 测试问题: {question}")
        try:
            result = parser.parse_intent(question)
            print(f"   意图类型: {result['intent']}")
            print(f"   需要分析: {result['need_data_analysis']}")
            print(f"   分析类型: {result['analysis_type']}")
            print(f"   复杂度: {result['complexity']}")
            print(f"   置信度: {result['confidence']}")
            print(f"   关键词: {result['keywords']}")
            
            # 检查是否符合预期
            if "销量" in question or "表现" in question or "业绩" in question:
                if result['need_data_analysis']:
                    print("   ✅ 正确识别为需要数据分析")
                else:
                    print("   ❌ 错误：应该需要数据分析但被识别为不需要")
            elif question in ["你好", "帮助"]:
                if not result['need_data_analysis']:
                    print("   ✅ 正确识别为不需要数据分析")
                else:
                    print("   ❌ 错误：不应该需要数据分析但被识别为需要")
                    
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")

if __name__ == "__main__":
    test_intent_recognition()