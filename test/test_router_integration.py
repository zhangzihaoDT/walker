#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由器集成测试
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.router import get_router

def test_router_integration():
    """测试路由器集成功能"""
    print("=== 路由器集成测试 ===")
    
    try:
        router = get_router()
        print("✅ 路由器初始化成功")
        
        # 测试1: query_only类型
        print("\n测试1: query_only路由")
        result = router.process_user_question("查询用户数据")
        print(f"问题: 查询用户数据")
        print(f"意图: {result.get('intent', {}).get('intent', 'unknown')}")
        print(f"执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"响应: {result.get('final_response', 'No response')[:100]}...")
        
        # 测试2: data_analysis类型
        print("\n测试2: data_analysis路由")
        result = router.process_user_question("分析数据统计信息")
        print(f"问题: 分析数据统计信息")
        print(f"意图: {result.get('intent', {}).get('intent', 'unknown')}")
        print(f"执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"响应: {result.get('final_response', 'No response')[:100]}...")
        
        # 测试3: general_chat类型
        print("\n测试3: general_chat路由")
        result = router.process_user_question("你好，今天天气怎么样？")
        print(f"问题: 你好，今天天气怎么样？")
        print(f"意图: {result.get('intent', {}).get('intent', 'unknown')}")
        print(f"执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"响应: {result.get('final_response', 'No response')[:100]}...")
        
        print("\n=== 路由器集成测试完成 ===")
        
    except Exception as e:
        print(f"❌ 路由器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_router_integration()