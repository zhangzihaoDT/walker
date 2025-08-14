#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM客户端模块 - 封装GLM模型调用逻辑
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class GLMClient:
    """GLM客户端类，封装模型调用和响应处理"""
    
    def __init__(self, model_type: str = "flash"):
        """
        初始化GLM客户端
        
        Args:
            model_type: 模型类型，"flash" 或 "plus"
        """
        self.model_type = model_type
        
        # 获取API密钥
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("未找到ZHIPU_API_KEY环境变量，请检查.env文件配置")
        
        if model_type == "flash":
            self.client = ChatOpenAI(
                model="glm-4-flash",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                api_key=api_key,
                temperature=0.1,
                max_tokens=4000
            )
        elif model_type == "plus":
            self.client = ChatOpenAI(
                model="glm-4-plus",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                api_key=api_key,
                temperature=0.1,
                max_tokens=4000
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        logger.info(f"GLM客户端初始化成功，模型类型: {model_type}")
    
    def generate_response(self, prompt: str) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示词
            
        Returns:
            生成的响应文本
        """
        try:
            message = HumanMessage(content=prompt)
            response = self.client.invoke([message])
            
            # 记录token使用情况
            if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
                token_usage = response.response_metadata['token_usage']
                total_tokens = token_usage.get('total_tokens', 0)
                logger.info(f"GLM调用成功，使用tokens: {total_tokens}")
            else:
                logger.info("GLM调用成功")
            
            return response.content
            
        except Exception as e:
            logger.error(f"GLM调用失败: {e}")
            raise
    
    def parse_json_response(self, prompt: str) -> Dict[str, Any]:
        """
        生成JSON格式的响应并解析
        
        Args:
            prompt: 输入提示词
            
        Returns:
            解析后的JSON字典，如果解析失败返回包含error字段的字典
        """
        try:
            response_text = self.generate_response(prompt)
            
            # 尝试提取JSON部分
            json_text = self._extract_json_from_text(response_text)
            
            # 解析JSON
            result = json.loads(json_text)
            logger.info(f"JSON解析成功: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始响应: {response_text}")
            return {
                "error": f"JSON解析失败: {str(e)}",
                "raw_response": response_text
            }
        except Exception as e:
            logger.error(f"响应生成失败: {e}")
            return {
                "error": f"响应生成失败: {str(e)}"
            }
    
    def _extract_json_from_text(self, text: str) -> str:
        """
        从文本中提取JSON部分
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            提取的JSON字符串
        """
        # 移除可能的markdown代码块标记
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        # 查找JSON对象的开始和结束
        start_idx = text.find('{')
        if start_idx == -1:
            raise ValueError("未找到JSON对象开始标记")
        
        # 从后往前查找最后一个}
        end_idx = text.rfind('}')
        if end_idx == -1 or end_idx <= start_idx:
            raise ValueError("未找到JSON对象结束标记")
        
        json_text = text[start_idx:end_idx + 1]
        return json_text.strip()


# 全局客户端实例
_glm_client = None

def get_glm_client(model_type: str = "flash") -> GLMClient:
    """
    获取GLM客户端实例（单例模式）
    
    Args:
        model_type: 模型类型
        
    Returns:
        GLM客户端实例
    """
    global _glm_client
    if _glm_client is None:
        _glm_client = GLMClient(model_type)
    return _glm_client


# 向后兼容的模型配置
glm_flash = None
glm_plus = None

def _get_legacy_client(model_type: str):
    """获取传统的模型客户端"""
    client = get_glm_client(model_type)
    return client.client

# 延迟初始化
def __getattr__(name):
    if name == "glm_flash":
        return _get_legacy_client("flash")
    elif name == "glm_plus":
        return _get_legacy_client("plus")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")