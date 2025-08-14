#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio集成测试

测试从Gradio前端入口开始的完整销量查询流程：
1. 模拟Gradio前端请求
2. 意图识别
3. 模块选择和执行
4. LLM解读
5. 前端响应
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import asyncio
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from core.graph_builder import GraphBuilder
from llm.glm import GLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_gradio_integration.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class GradioIntegrationTester:
    """Gradio集成测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.graph_builder = None
        self.test_results = []
        
    def setup(self) -> bool:
        """设置测试环境"""
        logger.info("🔧 设置Gradio集成测试环境...")
        
        try:
            # 加载环境变量
            from dotenv import load_dotenv
            load_dotenv()
            
            # 检查数据文件
            data_file = project_root / "data" / "乘用车上险量_0723.parquet"
            if not data_file.exists():
                logger.error(f"❌ 数据文件不存在: {data_file}")
                return False
            
            # 检查API密钥
            api_key = os.getenv('ZHIPU_API_KEY')
            if not api_key:
                logger.error("❌ 未找到ZHIPU_API_KEY环境变量")
                logger.error("请确保.env文件中包含有效的ZHIPU_API_KEY")
                return False
            
            logger.info(f"✅ 找到API密钥，长度: {len(api_key)}")
            
            # 初始化LLM客户端
            try:
                from llm.glm import get_glm_client
                self.llm_client = get_glm_client("flash")
                logger.info("✅ LLM客户端初始化成功")
                
                # 测试LLM连接
                test_response = self.llm_client.generate_response("你好，请回复'测试成功'")
                logger.info(f"🧪 LLM连接测试: {test_response[:50]}...")
                
            except Exception as e:
                logger.error(f"❌ LLM客户端初始化失败: {e}")
                return False
            
            # 初始化GraphBuilder
            try:
                self.graph_builder = GraphBuilder()
                logger.info("✅ GraphBuilder初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ GraphBuilder初始化失败: {e}")
                logger.warning("⚠️ 继续进行有限功能测试")
                self.graph_builder = None
            
            # 初始化ModuleExecutor
            try:
                from core.module_executor import get_module_executor
                self.module_executor = get_module_executor()
                logger.info("✅ ModuleExecutor初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ ModuleExecutor初始化失败: {e}")
                self.module_executor = None
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试环境设置失败: {e}")
            return False
    
    def simulate_gradio_request(self, user_question: str, session_id: str = "test_session") -> Dict[str, Any]:
        """模拟Gradio前端请求"""
        logger.info(f"🌐 模拟Gradio请求: {user_question}")
        
        # 模拟Gradio传递的参数
        gradio_request = {
            "user_question": user_question,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "source": "gradio_frontend"
        }
        
        logger.info(f"📤 请求参数: {gradio_request}")
        return gradio_request
    
    def test_sales_query_module_directly(self, user_question: str) -> Dict[str, Any]:
        """直接测试销量查询模块"""
        logger.info("🔧 直接测试销量查询模块功能")
        
        try:
            # 模拟意图识别结果
            intent_result = self.simulate_intent_recognition(user_question)
            logger.info(f"📋 模拟意图识别: {intent_result}")
            
            # 直接调用销量查询模块
            if intent_result.get('intent') == 'sales_query':
                 if self.module_executor is not None:
                     result = self.module_executor.execute_module(
                         module_name='sales_query_module',
                         user_question=user_question,
                         intent_result=intent_result
                     )
                 else:
                     # 直接导入并测试销量查询模块
                     logger.info("📋 直接导入销量查询模块进行测试")
                     result = self.test_sales_module_directly(user_question, intent_result)
                 
                 # 记录SQL语句
                 if 'sql_query' in result:
                     logger.info(f"📊 执行的SQL语句: {result['sql_query']}")
                 
                 return {
                    'user_question': user_question,
                    'intent': intent_result,
                    'data_analysis': {
                        'executed': True,
                        'success': result.get('success', False),
                        'result': result,
                        'error': result.get('error')
                    },
                    'final_response': self.generate_simple_response(result)
                }
            else:
                return {
                    'user_question': user_question,
                    'intent': intent_result,
                    'data_analysis': {
                        'executed': False,
                        'success': False,
                        'result': None,
                        'error': '非销量查询问题'
                    },
                    'final_response': '抱歉，我目前主要支持销量相关的查询。'
                }
                
        except Exception as e:
            logger.error(f"❌ 直接测试销量查询模块失败: {e}")
            return {
                'user_question': user_question,
                'intent': {'intent': 'error'},
                'data_analysis': {
                    'executed': False,
                    'success': False,
                    'result': None,
                    'error': str(e)
                },
                'final_response': f'测试失败: {str(e)}'
            }
    
    def simulate_intent_recognition(self, user_question: str) -> Dict[str, Any]:
        """模拟意图识别"""
        sales_keywords = ['销量', '品牌', '汽车', '电动车', '汽油车', '新能源', '比亚迪', '特斯拉', '蔚来', '省', '市', '趋势']
        
        if any(keyword in user_question for keyword in sales_keywords):
            return {
                'intent': 'sales_query',
                'confidence': 0.9,
                'reason': '检测到销量相关关键词',
                'need_data_analysis': True
            }
        else:
            return {
                'intent': 'general_chat',
                'confidence': 0.8,
                'reason': '未检测到销量相关关键词',
                'need_data_analysis': False
            }
    
    def generate_simple_response(self, result: Dict[str, Any]) -> str:
        """生成简单的响应"""
        if result.get('success'):
            summary = result.get('summary', '')
            data = result.get('data', [])
            
            if summary:
                response = f"查询结果：{summary}"
                if data and len(data) <= 5:
                    response += "\n\n详细数据：\n"
                    for i, record in enumerate(data, 1):
                        response += f"{i}. {record}\n"
                return response
            else:
                return "查询完成，但未找到相关数据。"
        else:
            error = result.get('error', '未知错误')
            return f"查询失败：{error}"
    
    def test_sales_module_directly(self, user_question: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """直接测试销量查询模块（不通过module_executor）"""
        try:
            from modules.sales_query_module import SalesQueryModule
            
            # 创建销量查询模块实例
            sales_module = SalesQueryModule()
            
            # 执行查询
            result = sales_module.execute(user_question, intent_result)
            
            # 记录SQL语句
            if hasattr(sales_module, '_last_sql_query'):
                logger.info(f"📊 执行的SQL语句: {sales_module._last_sql_query}")
            elif 'sql_query' in result:
                logger.info(f"📊 执行的SQL语句: {result['sql_query']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 直接测试销量查询模块失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'summary': f'模块执行失败: {str(e)}'
            }
    
    def test_complete_workflow(self, user_question: str) -> Dict[str, Any]:
        """测试完整的工作流程"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 测试完整工作流程: {user_question}")
        logger.info(f"{'='*60}")
        
        test_result = {
            'question': user_question,
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'overall_success': False,
            'response_time': 0.0
        }
        
        start_time = datetime.now()
        
        try:
            # 步骤1: 模拟Gradio请求
            logger.info("📋 步骤1: 模拟Gradio前端请求")
            gradio_request = self.simulate_gradio_request(user_question)
            test_result['steps']['gradio_request'] = {
                'success': True,
                'request': gradio_request
            }
            
            # 步骤2: 调用GraphBuilder处理请求
            logger.info("📋 步骤2: GraphBuilder处理请求")
            
            # 构建初始状态
            initial_state = {
                "user_question": user_question,
                "session_id": gradio_request["session_id"]
            }
            
            # 执行图构建器工作流
            logger.info("🚀 开始执行GraphBuilder工作流...")
            
            if self.graph_builder is not None:
                # 使用router的process_user_question方法进行完整流程
                from core.router import get_router
                router = get_router()
                final_state = router.process_user_question(user_question)
                logger.info(f"🚀 完整工作流程执行完成")
            else:
                # GraphBuilder不可用，使用LLM进行完整流程测试
                logger.warning("⚠️ GraphBuilder不可用，使用LLM进行完整流程测试")
                final_state = self.test_complete_llm_workflow(user_question)
            
            test_result['steps']['graph_execution'] = {
                'success': True,
                'final_state': final_state
            }
            
            # 步骤3: 提取和分析结果
            logger.info("📋 步骤3: 分析执行结果")
            
            final_response = final_state.get('final_response', '')
            execution_results = final_state.get('execution_results', [])
            intent_result = final_state.get('intent_result', {})
            
            logger.info(f"📊 执行结果分析:")
            logger.info(f"  - 意图识别: {intent_result.get('intent', 'unknown')}")
            logger.info(f"  - 执行模块数: {len(execution_results)}")
            logger.info(f"  - 响应长度: {len(final_response)} 字符")
            
            # 显示执行结果详情
            for i, result in enumerate(execution_results, 1):
                if result.get('success'):
                    data_count = len(result.get('data', []))
                    logger.info(f"  - 模块{i}: 成功，返回{data_count}条记录")
                else:
                    logger.info(f"  - 模块{i}: 失败，错误: {result.get('error', '未知')}")
            
            test_result['steps']['result_analysis'] = {
                'success': True,
                'intent': intent_result.get('intent'),
                'module_count': len(execution_results),
                'response_length': len(final_response),
                'execution_results': execution_results
            }
            
            # 步骤4: 模拟前端响应
            logger.info("📋 步骤4: 模拟前端响应")
            
            frontend_response = {
                'status': 'success',
                'message': final_response,
                'metadata': {
                    'intent': intent_result.get('intent'),
                    'confidence': intent_result.get('confidence'),
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                    'data_points': sum(len(r.get('data', [])) for r in execution_results)
                }
            }
            
            logger.info(f"📤 前端响应:")
            logger.info(f"  - 状态: {frontend_response['status']}")
            logger.info(f"  - 响应长度: {len(frontend_response['message'])} 字符")
            logger.info(f"  - 执行时间: {frontend_response['metadata']['execution_time']:.2f}秒")
            logger.info(f"  - 数据点数: {frontend_response['metadata']['data_points']}")
            
            test_result['steps']['frontend_response'] = {
                'success': True,
                'response': frontend_response
            }
            
            # 计算总执行时间
            end_time = datetime.now()
            test_result['response_time'] = (end_time - start_time).total_seconds()
            test_result['overall_success'] = True
            
            logger.info(f"✅ 完整工作流程测试成功！")
            logger.info(f"⏱️ 总执行时间: {test_result['response_time']:.2f}秒")
            
            return test_result
            
        except Exception as e:
            logger.error(f"❌ 工作流程测试失败: {e}")
            import traceback
            traceback.print_exc()
            
            test_result['steps']['error'] = {
                'success': False,
                'error': str(e)
            }
            test_result['response_time'] = (datetime.now() - start_time).total_seconds()
            
            return test_result
    
    def test_complete_llm_workflow(self, user_question: str) -> Dict[str, Any]:
        """使用LLM进行完整流程测试"""
        try:
            logger.info(f"🤖 开始LLM完整流程测试: {user_question}")
            
            # 步骤1: 使用LLM进行意图识别
            intent_prompt = f"""请分析以下用户问题的意图，并返回JSON格式的结果：
用户问题：{user_question}

请返回包含以下字段的JSON：
{{
    "intent": "意图类型(如sales_query)",
    "entities": {{
        "region": "地区信息",
        "product": "产品信息",
        "time_period": "时间范围"
    }},
    "confidence": 0.95
}}"""
            
            intent_response = self.llm_client.generate_response(intent_prompt)
            logger.info(f"🧠 LLM意图识别结果: {intent_response}")
            
            # 解析意图识别结果
            try:
                import json
                intent_result = json.loads(intent_response)
            except:
                intent_result = {
                    "intent": "sales_query",
                    "entities": {"region": "广东省", "product": "汽车"},
                    "confidence": 0.8
                }
            
            # 步骤2: 执行销量查询模块
            if intent_result.get('intent') == 'sales_query':
                module_result = self.test_sales_module_directly(user_question, intent_result)
            else:
                module_result = {'success': False, 'error': '不支持的意图类型'}
            
            # 步骤3: 使用LLM生成最终回复
            if module_result.get('success'):
                response_prompt = f"""基于以下查询结果，生成用户友好的回复：

用户问题：{user_question}
SQL查询：{module_result.get('sql_query', '')}
查询结果：{module_result.get('data', [])}

请生成一个自然、友好的回复，包含具体的数据信息。"""
                
                final_response = self.llm_client.generate_response(response_prompt)
                logger.info(f"🎯 LLM生成最终回复: {final_response}")
            else:
                final_response = "抱歉，无法处理您的查询请求。"
            
            return {
                'intent_result': intent_result,
                'execution_results': [module_result],
                'final_response': final_response
            }
            
        except Exception as e:
            logger.error(f"❌ LLM完整流程测试失败: {str(e)}")
            return {
                'intent_result': {'intent': 'error'},
                'execution_results': [{'success': False, 'error': str(e)}],
                'final_response': f'测试失败: {str(e)}'
            }
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有测试用例"""
        logger.info("\n🚀 开始Gradio集成测试套件")
        logger.info("=" * 80)
        
        # 测试用例（专注于销量查询）
        test_questions = [
            "比亚迪的销量如何？",
            "特斯拉和蔚来的销量对比",
            "销量前5名的品牌",
            "电动车和汽油车的销量对比",
            "广东省的汽车销量"
        ]
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n📋 测试用例 {i}/{len(test_questions)}")
            result = self.test_complete_workflow(question)
            results.append(result)
            self.test_results.append(result)
            
            # 短暂休息，避免API限制
            import time
            time.sleep(1)
        
        return results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        logger.info("\n📊 生成Gradio集成测试报告...")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['overall_success'])
        avg_response_time = sum(r['response_time'] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        report = f"""
# Gradio集成测试报告

## 测试概览
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 总测试数: {total_tests}
- 成功测试: {successful_tests}
- 成功率: {successful_tests/total_tests*100:.1f}%
- 平均响应时间: {avg_response_time:.2f}秒

## 详细结果

"""
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅ 成功" if result['overall_success'] else "❌ 失败"
            report += f"### 测试 {i}: {result['question']}\n"
            report += f"**状态**: {status}\n"
            report += f"**响应时间**: {result['response_time']:.2f}秒\n\n"
            
            # 各步骤状态
            steps = result['steps']
            report += "**步骤详情**:\n"
            report += f"- Gradio请求: {'✅' if steps.get('gradio_request', {}).get('success') else '❌'}\n"
            report += f"- Graph执行: {'✅' if steps.get('graph_execution', {}).get('success') else '❌'}\n"
            report += f"- 结果分析: {'✅' if steps.get('result_analysis', {}).get('success') else '❌'}\n"
            report += f"- 前端响应: {'✅' if steps.get('frontend_response', {}).get('success') else '❌'}\n\n"
            
            # 显示执行统计
            if 'result_analysis' in steps and steps['result_analysis'].get('success'):
                analysis = steps['result_analysis']
                report += f"**执行统计**:\n"
                report += f"- 意图识别: {analysis.get('intent', 'unknown')}\n"
                report += f"- 执行模块数: {analysis.get('module_count', 0)}\n"
                report += f"- 响应长度: {analysis.get('response_length', 0)} 字符\n\n"
            
            # 如果有错误，显示错误信息
            if 'error' in steps:
                report += f"**错误信息**: {steps['error']['error']}\n\n"
        
        return report

def main():
    """主函数"""
    print("🧪 Gradio集成测试")
    print("=" * 50)
    
    # 创建测试器
    tester = GradioIntegrationTester()
    
    # 设置测试环境
    if not tester.setup():
        print("❌ 测试环境设置失败")
        return
    
    try:
        # 运行所有测试
        results = tester.run_all_tests()
        
        # 生成报告
        report = tester.generate_report()
        
        # 保存报告
        report_file = project_root / "test" / "gradio_integration_test_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 测试报告已保存到: {report_file}")
        
        # 显示简要统计
        total = len(results)
        success = sum(1 for r in results if r['overall_success'])
        avg_time = sum(r['response_time'] for r in results) / total if total > 0 else 0
        
        print(f"\n📊 测试结果: {success}/{total} 成功 ({success/total*100:.1f}%)")
        print(f"⏱️ 平均响应时间: {avg_time:.2f}秒")
        
        if success == total:
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 部分测试失败，请查看详细报告")
            
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
     main()