#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据聊天系统测试模块
"""

import sys
import unittest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm.glm import GLMClient
from core.router import DataChatWorkflow
from modules.run_data_describe import DataAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataChatSystem(unittest.TestCase):
    """数据聊天系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_questions = [
            "你好",
            "你有什么数据？",
            "数据范围有哪些？",
            "请分析一下数据",
            "数据质量如何？",
            "有多少条记录？"
        ]
    
    def test_data_analyzer(self):
        """测试数据分析器"""
        print("\n🧪 测试数据分析器...")
        
        try:
            analyzer = DataAnalyzer()
            data_files = analyzer.get_data_files()
            
            self.assertGreater(len(data_files), 0, "应该找到至少一个数据文件")
            print(f"✅ 找到 {len(data_files)} 个数据文件")
            
            # 测试读取第一个CSV文件
            csv_files = [f for f in data_files if f.suffix.lower() == '.csv']
            if csv_files:
                df = analyzer.read_csv_file(csv_files[0])
                self.assertIsNotNone(df, "CSV文件应该能够成功读取")
                self.assertGreater(df.shape[0], 0, "数据应该包含行")
                print(f"✅ CSV文件读取成功: {df.shape}")
            
        except Exception as e:
            self.fail(f"数据分析器测试失败: {e}")
    
    @patch('llm.glm.ZhipuAI')
    def test_glm_client(self, mock_zhipu):
        """测试GLM客户端（使用模拟）"""
        print("\n🧪 测试GLM客户端...")
        
        # 模拟GLM响应
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "你好！我是GLM-4助手。"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 15
        mock_response.usage.total_tokens = 25
        mock_response.model = "glm-4"
        mock_response.choices[0].finish_reason = "stop"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_zhipu.return_value = mock_client
        
        try:
            # 设置环境变量
            import os
            os.environ['ZHIPU_API_KEY'] = 'test_key'
            
            client = GLMClient()
            result = client.simple_chat("你好")
            
            self.assertIsInstance(result, str, "应该返回字符串响应")
            self.assertGreater(len(result), 0, "响应不应该为空")
            print(f"✅ GLM客户端测试成功: {result[:50]}...")
            
        except Exception as e:
            self.fail(f"GLM客户端测试失败: {e}")
    
    @patch('core.graph_builder.get_glm_client')
    def test_workflow_intent_recognition(self, mock_get_glm):
        """测试工作流意图识别"""
        print("\n🧪 测试工作流意图识别...")
        
        # 模拟GLM客户端
        mock_client = MagicMock()
        mock_client.parse_json_response.return_value = {
            "intent": "data_query",
            "confidence": 0.9,
            "reason": "用户询问数据相关问题",
            "need_data_analysis": True
        }
        mock_get_glm.return_value = mock_client
        
        try:
            workflow = DataChatWorkflow()
            
            for question in self.test_questions:
                intent_result = workflow.recognize_intent(question)
                
                self.assertIn("intent", intent_result, "应该包含意图字段")
                self.assertIn("confidence", intent_result, "应该包含置信度字段")
                self.assertIn("need_data_analysis", intent_result, "应该包含数据分析需求字段")
                
                print(f"✅ 意图识别成功: {question} -> {intent_result['intent']}")
            
        except Exception as e:
            self.fail(f"工作流意图识别测试失败: {e}")
    
    @patch('core.graph_builder.get_glm_client')
    def test_workflow_complete_process(self, mock_get_glm):
        """测试完整工作流程"""
        print("\n🧪 测试完整工作流程...")
        
        # 模拟GLM客户端
        mock_client = MagicMock()
        
        # 模拟意图识别响应
        mock_client.parse_json_response.return_value = {
            "intent": "data_query",
            "confidence": 0.9,
            "reason": "用户询问数据相关问题",
            "need_data_analysis": True
        }
        
        # 模拟最终响应生成
        mock_client.simple_chat.return_value = "根据数据分析结果，我们有以下数据集..."
        
        mock_get_glm.return_value = mock_client
        
        try:
            workflow = DataChatWorkflow()
            
            test_question = "你有什么数据？"
            result = workflow.process_user_question(test_question)
            
            # 验证返回结果结构
            self.assertIn("user_question", result, "应该包含用户问题")
            self.assertIn("intent", result, "应该包含意图识别结果")
            self.assertIn("data_analysis", result, "应该包含数据分析结果")
            self.assertIn("final_response", result, "应该包含最终响应")
            
            self.assertEqual(result["user_question"], test_question, "用户问题应该匹配")
            self.assertIsInstance(result["final_response"], str, "最终响应应该是字符串")
            self.assertGreater(len(result["final_response"]), 0, "最终响应不应该为空")
            
            print(f"✅ 完整工作流程测试成功")
            print(f"   问题: {test_question}")
            print(f"   意图: {result['intent']['intent']}")
            print(f"   响应: {result['final_response'][:100]}...")
            
        except Exception as e:
            self.fail(f"完整工作流程测试失败: {e}")
    
    def test_prompts_loading(self):
        """测试提示词加载"""
        print("\n🧪 测试提示词加载...")
        
        try:
            from llm.prompts import (
                INTENT_RECOGNITION_PROMPT,
                DATA_ANALYSIS_EXPLANATION_PROMPT,
                GENERAL_CHAT_PROMPT,
                ERROR_HANDLING_PROMPT
            )
            
            prompts = [
                ("意图识别", INTENT_RECOGNITION_PROMPT),
                ("数据分析解释", DATA_ANALYSIS_EXPLANATION_PROMPT),
                ("一般对话", GENERAL_CHAT_PROMPT),
                ("错误处理", ERROR_HANDLING_PROMPT)
            ]
            
            for name, prompt in prompts:
                self.assertIsInstance(prompt, str, f"{name}提示词应该是字符串")
                self.assertGreater(len(prompt), 0, f"{name}提示词不应该为空")
                self.assertIn("{user_question}", prompt, f"{name}提示词应该包含用户问题占位符")
                print(f"✅ {name}提示词加载成功")
            
        except Exception as e:
            self.fail(f"提示词加载测试失败: {e}")


def run_integration_test():
    """运行集成测试"""
    print("\n" + "="*60)
    print("🚀 开始数据聊天系统集成测试")
    print("="*60)
    
    try:
        # 测试各个组件
        print("\n📋 测试组件列表:")
        print("1. 数据分析器 (DataAnalyzer)")
        print("2. GLM客户端 (GLMClient)")
        print("3. 工作流程 (DataChatWorkflow)")
        print("4. 提示词模块 (Prompts)")
        
        # 运行单元测试
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDataChatSystem)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("\n" + "="*60)
            print("🎉 所有测试通过！系统准备就绪")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ 部分测试失败，请检查错误信息")
            print("="*60)
            return False
            
    except Exception as e:
        print(f"\n❌ 集成测试执行失败: {e}")
        return False


if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)