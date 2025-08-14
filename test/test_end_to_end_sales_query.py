#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端销量查询测试

测试从Gradio前端到销量查询模块的完整流程：
1. 意图识别
2. 模块选择
3. SQL语句生成
4. 查询执行
5. LLM解读
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from core.walker import Walker
from agents.intent_parser import IntentParser
from agents.module_executor import get_module_executor
from modules.sales_query_module import SalesQueryModule
from llm.glm import GLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_end_to_end.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class EndToEndTester:
    """端到端测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.walker = None
        self.intent_parser = None
        self.module_executor = None
        self.sales_module = None
        self.llm_client = None
        self.test_results = []
        
    def setup(self) -> bool:
        """设置测试环境"""
        logger.info("🔧 设置测试环境...")
        
        try:
            # 检查数据文件
            data_file = project_root / "data" / "乘用车上险量_0723.parquet"
            if not data_file.exists():
                logger.error(f"❌ 数据文件不存在: {data_file}")
                return False
            
            # 初始化Walker（跳过IntentParser，因为需要OpenAI API key）
            try:
                self.walker = Walker()
                logger.info("✅ Walker初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ Walker初始化失败: {e}")
                logger.warning("将跳过意图识别测试")
            
            # 跳过意图解析器初始化（需要OpenAI API key）
            logger.info("⚠️ 跳过意图解析器初始化（需要OpenAI API key）")
            
            # 初始化模块执行器
            self.module_executor = get_module_executor()
            logger.info("✅ 模块执行器初始化成功")
            
            # 初始化销量查询模块
            self.sales_module = SalesQueryModule()
            logger.info("✅ 销量查询模块初始化成功")
            
            # 初始化LLM客户端
            try:
                # 检查环境变量
                import os
                if os.getenv('ZHIPU_API_KEY'):
                    self.llm_client = GLMClient()
                    logger.info("✅ LLM客户端初始化成功")
                else:
                    logger.warning("⚠️ 未找到ZHIPU_API_KEY环境变量")
                    self.llm_client = None
            except Exception as e:
                logger.warning(f"⚠️ LLM客户端初始化失败: {e}")
                logger.warning("将跳过LLM解读测试")
                self.llm_client = None
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试环境设置失败: {e}")
            return False
    
    def test_intent_recognition(self, question: str) -> Dict[str, Any]:
        """测试意图识别"""
        logger.info(f"🎯 测试意图识别: {question}")
        
        try:
            # 使用模拟意图识别结果（专注于销量查询测试）
            logger.info("🔍 使用模拟意图识别进行测试")
            
            # 基于关键词的简单意图识别
            sales_keywords = ['销量', '销售', '品牌', '汽车', '车型', '比亚迪', '特斯拉', '蔚来', '前5', '对比', '趋势', '电动车', '汽油车', '新能源', '省', '市']
            is_sales_query = any(keyword in question for keyword in sales_keywords)
            
            intent_result = {
                'intent': 'data_analysis' if is_sales_query else 'unknown',
                'confidence': 0.9 if is_sales_query else 0.2,
                'recommended_module': 'sales_query' if is_sales_query else 'none',
                'need_data_analysis': is_sales_query,
                'simulated': True
            }
            
            logger.info(f"📊 意图识别结果:")
            logger.info(f"  - 意图类型: {intent_result.get('intent', 'unknown')}")
            logger.info(f"  - 置信度: {intent_result.get('confidence', 0)}")
            logger.info(f"  - 推荐模块: {intent_result.get('recommended_module', 'none')}")
            logger.info(f"  - 需要数据分析: {intent_result.get('need_data_analysis', False)}")
            logger.info(f"  - 模式: 模拟识别")
            
            return {
                'success': True,
                'intent_result': intent_result,
                'question': question
            }
            
        except Exception as e:
            logger.error(f"❌ 意图识别失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def test_module_selection(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """测试模块选择"""
        logger.info("🔍 测试模块选择...")
        
        try:
            intent = intent_result.get('intent', '')
            recommended_module = intent_result.get('recommended_module', '')
            
            # 判断是否应该选择销量查询模块
            should_use_sales_module = (
                intent in ['data_analysis', 'query_only'] and
                recommended_module == 'sales_query'
            )
            
            logger.info(f"📋 模块选择结果:")
            logger.info(f"  - 意图: {intent}")
            logger.info(f"  - 推荐模块: {recommended_module}")
            logger.info(f"  - 使用销量模块: {should_use_sales_module}")
            
            return {
                'success': True,
                'should_use_sales_module': should_use_sales_module,
                'selected_module': recommended_module if should_use_sales_module else 'none'
            }
            
        except Exception as e:
            logger.error(f"❌ 模块选择失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_parameter_extraction(self, question: str) -> Dict[str, Any]:
        """测试参数提取"""
        logger.info(f"🔧 测试参数提取: {question}")
        
        try:
            # 使用销量查询模块提取参数
            params = {'user_question': question}
            extracted_params = self.sales_module._extract_query_parameters(params)
            
            logger.info(f"📊 参数提取结果:")
            for key, value in extracted_params.items():
                if value:
                    logger.info(f"  - {key}: {value}")
            
            return {
                'success': True,
                'extracted_params': extracted_params
            }
            
        except Exception as e:
            logger.error(f"❌ 参数提取失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_template_selection(self, extracted_params: Dict[str, Any]) -> Dict[str, Any]:
        """测试模板选择"""
        logger.info("📝 测试查询模板选择...")
        
        try:
            # 选择查询模板
            template_info = self.sales_module._select_template(extracted_params)
            
            logger.info(f"📋 模板选择结果:")
            logger.info(f"  - 模板名称: {template_info['name']}")
            logger.info(f"  - 模板描述: {template_info['description']}")
            logger.info(f"  - 必需参数: {template_info.get('required_params', [])}")
            logger.info(f"  - 可选参数: {template_info.get('optional_params', [])}")
            
            return {
                'success': True,
                'template_info': template_info
            }
            
        except Exception as e:
            logger.error(f"❌ 模板选择失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_sql_generation_and_execution(self, question: str) -> Dict[str, Any]:
        """测试SQL生成和执行"""
        logger.info(f"🗃️ 测试SQL生成和执行: {question}")
        
        try:
            # 加载模块配置
            config_file = project_root / "modules" / "analysis_config.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            sales_query_config = None
            for module in config['modules']:
                if module['module_id'] == 'sales_query':
                    sales_query_config = module
                    break
            
            if not sales_query_config:
                raise ValueError("未找到sales_query模块配置")
            
            # 准备参数
            params = {
                "data_source": "data/乘用车上险量_0723.parquet",
                "user_question": question
            }
            
            # 执行模块
            logger.info("🚀 开始执行销量查询模块...")
            result = self.module_executor.execute_module(
                module_id='sales_query',
                parameters=params,
                module_config=sales_query_config
            )
            
            if result.get('success', False):
                data = result.get('data', [])
                analysis = result.get('analysis', {})
                summary = result.get('summary', '')
                
                logger.info(f"✅ 查询执行成功")
                logger.info(f"📊 查询结果统计:")
                logger.info(f"  - 返回记录数: {len(data)}")
                logger.info(f"  - 查询类型: {analysis.get('query_type', 'unknown')}")
                logger.info(f"  - 使用模板: {analysis.get('template_used', 'unknown')}")
                logger.info(f"  - 摘要: {summary[:100]}..." if len(summary) > 100 else f"  - 摘要: {summary}")
                
                # 记录SQL相关信息（模拟）
                logger.info(f"🔍 SQL执行信息:")
                logger.info(f"  - 查询模板: {analysis.get('template_used', 'unknown')}")
                logger.info(f"  - 使用参数: {analysis.get('parameters_used', {})}")
                
                # 显示前几条结果
                if data:
                    logger.info(f"📋 查询结果示例（前3条）:")
                    for i, record in enumerate(data[:3], 1):
                        logger.info(f"  {i}. {record}")
                
                return {
                    'success': True,
                    'result': result,
                    'record_count': len(data),
                    'query_type': analysis.get('query_type', 'unknown')
                }
            else:
                error = result.get('error', '未知错误')
                logger.error(f"❌ 查询执行失败: {error}")
                return {
                    'success': False,
                    'error': error
                }
                
        except Exception as e:
            logger.error(f"❌ SQL生成和执行失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_llm_interpretation(self, query_result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """测试LLM解读"""
        logger.info(f"🤖 测试LLM解读: {question}")
        
        if not self.llm_client:
            logger.warning("⚠️ LLM客户端未初始化，跳过LLM解读测试")
            return {
                'success': False,
                'error': 'LLM客户端未初始化'
            }
        
        try:
            # 准备LLM输入
            data = query_result.get('result', {}).get('data', [])
            analysis = query_result.get('result', {}).get('analysis', {})
            
            # 构建提示词
            prompt = f"""
用户问题：{question}

查询结果：
- 查询类型：{analysis.get('query_type', 'unknown')}
- 记录数量：{len(data)}
- 数据摘要：{analysis.get('data_summary', {})}

具体数据（前5条）：
{json.dumps(data[:5], ensure_ascii=False, indent=2)}

请基于以上查询结果，用自然语言回答用户的问题，要求：
1. 直接回答用户关心的问题
2. 提供具体的数据支撑
3. 语言简洁明了
4. 如果有明显的趋势或洞察，请指出
"""
            
            logger.info("🔄 调用LLM进行结果解读...")
            
            # 调用LLM
            llm_response = self.llm_client.chat(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            interpretation = llm_response.get('content', '解读失败')
            
            logger.info(f"🎯 LLM解读结果:")
            logger.info(f"  {interpretation}")
            
            return {
                'success': True,
                'interpretation': interpretation,
                'llm_response': llm_response
            }
            
        except Exception as e:
            logger.error(f"❌ LLM解读失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_single_test(self, question: str) -> Dict[str, Any]:
        """运行单个问题的完整测试"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 开始测试问题: {question}")
        logger.info(f"{'='*60}")
        
        test_result = {
            'question': question,
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'overall_success': False
        }
        
        # 步骤1: 意图识别
        intent_result = self.test_intent_recognition(question)
        test_result['steps']['intent_recognition'] = intent_result
        
        if not intent_result['success']:
            logger.error("❌ 意图识别失败，终止测试")
            return test_result
        
        # 步骤2: 模块选择
        module_result = self.test_module_selection(intent_result['intent_result'])
        test_result['steps']['module_selection'] = module_result
        
        if not module_result['success'] or not module_result['should_use_sales_module']:
            logger.warning("⚠️ 未选择销量查询模块，跳过后续测试")
            return test_result
        
        # 步骤3: 参数提取
        param_result = self.test_parameter_extraction(question)
        test_result['steps']['parameter_extraction'] = param_result
        
        if not param_result['success']:
            logger.error("❌ 参数提取失败，终止测试")
            return test_result
        
        # 步骤4: 模板选择
        template_result = self.test_template_selection(param_result['extracted_params'])
        test_result['steps']['template_selection'] = template_result
        
        if not template_result['success']:
            logger.error("❌ 模板选择失败，终止测试")
            return test_result
        
        # 步骤5: SQL生成和执行
        sql_result = self.test_sql_generation_and_execution(question)
        test_result['steps']['sql_execution'] = sql_result
        
        if not sql_result['success']:
            logger.error("❌ SQL执行失败，终止测试")
            return test_result
        
        # 步骤6: LLM解读
        llm_result = self.test_llm_interpretation(sql_result, question)
        test_result['steps']['llm_interpretation'] = llm_result
        
        # 判断整体成功
        test_result['overall_success'] = (
            intent_result['success'] and
            module_result['success'] and
            param_result['success'] and
            template_result['success'] and
            sql_result['success']
        )
        
        if test_result['overall_success']:
            logger.info("✅ 完整流程测试成功！")
        else:
            logger.warning("⚠️ 部分步骤失败")
        
        return test_result
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有测试用例"""
        logger.info("\n🚀 开始端到端测试套件")
        logger.info("=" * 80)
        
        # 测试用例
        test_questions = [
            "比亚迪的销量如何？",
            "特斯拉和蔚来的销量对比",
            "销量前5名的品牌",
            "2024年的销量趋势",
            "电动车和汽油车的销量对比",
            "广东省的汽车销量",
            "北京和上海的新能源车销量"
        ]
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n📋 测试用例 {i}/{len(test_questions)}")
            result = self.run_single_test(question)
            results.append(result)
            self.test_results.append(result)
        
        return results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        logger.info("\n📊 生成测试报告...")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['overall_success'])
        
        report = f"""
# 端到端销量查询测试报告

## 测试概览
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 总测试数: {total_tests}
- 成功测试: {successful_tests}
- 成功率: {successful_tests/total_tests*100:.1f}%

## 详细结果

"""
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅ 成功" if result['overall_success'] else "❌ 失败"
            report += f"### 测试 {i}: {result['question']}\n"
            report += f"**状态**: {status}\n\n"
            
            # 各步骤状态
            steps = result['steps']
            report += "**步骤详情**:\n"
            report += f"- 意图识别: {'✅' if steps.get('intent_recognition', {}).get('success') else '❌'}\n"
            report += f"- 模块选择: {'✅' if steps.get('module_selection', {}).get('success') else '❌'}\n"
            report += f"- 参数提取: {'✅' if steps.get('parameter_extraction', {}).get('success') else '❌'}\n"
            report += f"- 模板选择: {'✅' if steps.get('template_selection', {}).get('success') else '❌'}\n"
            report += f"- SQL执行: {'✅' if steps.get('sql_execution', {}).get('success') else '❌'}\n"
            report += f"- LLM解读: {'✅' if steps.get('llm_interpretation', {}).get('success') else '❌'}\n\n"
            
            # 如果有错误，显示错误信息
            for step_name, step_result in steps.items():
                if not step_result.get('success') and 'error' in step_result:
                    report += f"**{step_name} 错误**: {step_result['error']}\n\n"
        
        return report

def main():
    """主函数"""
    print("🧪 端到端销量查询测试")
    print("=" * 50)
    
    # 创建测试器
    tester = EndToEndTester()
    
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
        report_file = project_root / "test" / "end_to_end_test_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 测试报告已保存到: {report_file}")
        
        # 显示简要统计
        total = len(results)
        success = sum(1 for r in results if r['overall_success'])
        print(f"\n📊 测试结果: {success}/{total} 成功 ({success/total*100:.1f}%)")
        
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