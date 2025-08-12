#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意图识别调试脚本
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

from llm.glm import get_glm_client
from llm.prompts import INTENT_RECOGNITION_PROMPT

def test_intent_recognition():
    """测试意图识别"""
    print("🔍 开始测试意图识别...")
    
    # 初始化GLM客户端
    glm_client = get_glm_client()
    
    # 测试问题
    test_questions = [
        "你好",
        "你有什么数据？",
        "数据范围有哪些？"
    ]
    
    for question in test_questions:
        print(f"\n📝 测试问题: {question}")
        
        # 生成提示词
        prompt = INTENT_RECOGNITION_PROMPT.format(user_question=question)
        print(f"\n📋 提示词:\n{prompt}")
        
        # 调用GLM生成响应
        try:
            response = glm_client.generate_response(prompt)
            print(f"\n🤖 GLM原始响应:\n{response}")
            
            # 尝试解析JSON
            result = glm_client.parse_json_response(prompt)
            print(f"\n✅ JSON解析结果:\n{result}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_intent_recognition()