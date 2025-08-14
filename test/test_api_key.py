#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API密钥测试脚本

测试智谱AI API密钥是否有效
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

def test_api_key():
    """测试API密钥有效性"""
    print("🔑 测试智谱AI API密钥...")
    
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 未找到ZHIPU_API_KEY环境变量")
        return False
    
    print(f"📋 API密钥长度: {len(api_key)}")
    print(f"📋 API密钥前缀: {api_key[:20]}")
    print(f"📋 API密钥后缀: {api_key[-20:]}")
    print(f"📋 完整API密钥: {api_key}")
    
    # 测试API调用
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "glm-4-flash",
        "messages": [
            {
                "role": "user",
                "content": "你好"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"📡 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API密钥有效！")
            print(f"🤖 响应: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"📄 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def check_env_file():
    """检查.env文件"""
    print("\n📁 检查.env文件...")
    
    env_path = project_root / ".env"
    if not env_path.exists():
        print("❌ .env文件不存在")
        return False
    
    print(f"✅ .env文件存在: {env_path}")
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "ZHIPU_API_KEY" in content:
            print("✅ .env文件包含ZHIPU_API_KEY")
            return True
        else:
            print("❌ .env文件不包含ZHIPU_API_KEY")
            return False

if __name__ == "__main__":
    print("🧪 智谱AI API密钥测试")
    print("=" * 40)
    
    # 检查环境文件
    env_ok = check_env_file()
    
    if env_ok:
        # 测试API密钥
        api_ok = test_api_key()
        
        if api_ok:
            print("\n🎉 所有测试通过！API密钥配置正确。")
        else:
            print("\n⚠️ API密钥可能已过期或无效，请检查智谱AI控制台。")
    else:
        print("\n❌ 环境配置有问题，请检查.env文件。")