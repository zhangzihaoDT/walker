#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walker模块 - 策略生成和执行协调器

根据用户输入的意图、所有可用的分析模块和要使用的数据库，
输出"策略集"（strategy list），包含：模块实例、参数候选、所属数据库信息。
支持策略执行结果聚合和反馈，支持后续跟进流程生成。
"""

import json
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModuleStrategy:
    """模块策略数据类"""
    module_id: str
    module_name: str
    module_instance: Any
    parameters: Dict[str, Any]
    database_info: Dict[str, Any]
    compatibility_score: float
    priority: int = 0
    estimated_execution_time: float = 0.0
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class StrategyExecutionResult:
    """策略执行结果数据类"""
    strategy: ModuleStrategy
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    insights: List[str] = None
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []


class Walker:
    """Walker策略生成器
    
    负责根据用户意图和可用资源生成最优的分析策略组合
    """
    
    def __init__(self, modules_config_path: str = None):
        """初始化Walker
        
        Args:
            modules_config_path: 模块配置文件路径
        """
        if modules_config_path is None:
            # 默认使用modules目录下的配置文件
            project_root = Path(__file__).parent.parent
            modules_config_path = project_root / "modules" / "analysis_config.json"
        
        self.modules_config_path = Path(modules_config_path)
        self.registered_modules = {}
        self.available_databases = []
        self.execution_history = []
        self.modules = {}  # 兼容性属性
        
        # 加载模块配置
        self._load_modules_config()
        
        # 设置默认数据库
        self._setup_default_databases()
    
    def _load_modules_config(self):
        """加载模块配置文件"""
        try:
            with open(self.modules_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.modules_metadata = config.get('modules', [])
            logger.info(f"加载了 {len(self.modules_metadata)} 个模块配置")
            
            # 自动注册配置文件中的模块
            self._auto_register_modules()
            
        except FileNotFoundError:
            logger.error(f"模块配置文件不存在: {self.modules_config_path}")
            self.modules_metadata = []
        except json.JSONDecodeError as e:
            logger.error(f"模块配置文件格式错误: {e}")
            self.modules_metadata = []
    
    def _auto_register_modules(self):
        """自动注册配置文件中的模块"""
        logger.info(f"开始自动注册模块，配置文件中有 {len(self.modules_metadata)} 个模块")
        
        for module_config in self.modules_metadata:
            try:
                module_id = module_config.get('module_id')
                if module_id:
                    # 将模块信息添加到registered_modules
                    self.registered_modules[module_id] = {
                        'info': module_config,
                        'instance': None  # 延迟实例化
                    }
                    logger.info(f"自动注册模块: {module_id} - {module_config.get('module_name', 'Unknown')}")
                else:
                    logger.warning(f"模块配置缺少module_id: {module_config}")
            except Exception as e:
                logger.error(f"自动注册模块失败: {e}")
        
        logger.info(f"模块注册完成，共注册了 {len(self.registered_modules)} 个模块")
    
    def _setup_default_databases(self):
        """
        设置默认数据库配置
        """
        default_databases = [
            {
                "name": "local_csv_data",
                "type": "csv",
                "path": "data",
                "description": "本地CSV数据目录",
                "fields": ["sales_volume", "company", "year", "month", "region"],  # 示例字段
                "supported_formats": ["csv"]
            },
            {
                "name": "local_parquet_data",
                "type": "parquet",
                "path": "data",
                "description": "本地Parquet数据目录",
                "fields": ["sales_volume", "company", "year", "month", "region"],  # 示例字段
                "supported_formats": ["parquet"]
            }
        ]
        
        self.available_databases = default_databases
        logger.info(f"设置了 {len(default_databases)} 个默认数据库")
    
    def register_module(self, module_class: Any, module_config: Dict[str, Any] = None):
        """注册分析模块
        
        Args:
            module_class: 模块类
            module_config: 模块配置信息
        """
        try:
            # 创建模块实例
            module_instance = module_class()
            
            # 获取模块信息
            module_info = module_instance.get_module_info()
            module_id = module_info['module_id']
            
            self.registered_modules[module_id] = {
                'instance': module_instance,
                'class': module_class,
                'info': module_info,
                'config': module_config or {}
            }
            
            logger.info(f"注册模块: {module_id} - {module_info['module_name']}")
            
        except Exception as e:
            logger.error(f"注册模块失败: {e}")
    
    def auto_discover_modules(self):
        """自动发现并注册modules目录下的模块"""
        modules_dir = self.modules_config_path.parent
        
        for module_meta in self.modules_metadata:
            try:
                # 构建模块路径
                file_path = module_meta.get('file_path', '')
                if not file_path:
                    continue
                
                # 转换文件路径为模块路径
                module_path = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
                
                # 动态导入模块
                module = importlib.import_module(module_path)
                
                # 获取模块类
                class_name = module_meta.get('class_name')
                if hasattr(module, class_name):
                    module_class = getattr(module, class_name)
                    self.register_module(module_class, module_meta)
                else:
                    logger.warning(f"模块 {module_path} 中未找到类 {class_name}")
                    
            except ImportError as e:
                logger.error(f"导入模块失败 {module_meta.get('file_path', '')}: {e}")
            except Exception as e:
                logger.error(f"注册模块失败 {module_meta.get('module_id', '')}: {e}")
    
    def set_available_databases(self, databases: List[Dict[str, Any]]):
        """设置可用的数据库列表
        
        Args:
            databases: 数据库信息列表
            [
                {
                    "type": "csv",
                    "path": "/path/to/data.csv",
                    "fields": ["col1", "col2", ...],
                    "connector": db_connector_object
                },
                ...
            ]
        """
        self.available_databases = databases
        logger.info(f"设置了 {len(databases)} 个可用数据库")
    
    def add_database(self, name: str, db_info: Dict[str, Any]):
        """
        添加数据库
        
        Args:
            name: 数据库名称
            db_info: 数据库信息
        """
        db_info['name'] = name
        self.available_databases.append(db_info)
        logger.info(f"添加数据库: {name}")
    
    def generate_strategies(self, 
                          user_intent: Dict[str, Any], 
                          max_strategies: int = 5,
                          min_compatibility_score: float = 0.5) -> List[ModuleStrategy]:
        """根据用户意图生成策略集
        
        Args:
            user_intent: 用户意图字典
                {
                    "action": "analyze",  # 动作类型
                    "target": "data_description",  # 分析目标
                    "parameters": {...},  # 参数
                    "data_source": "...",  # 数据源
                    "preferences": {...},  # 用户偏好
                    "analysis_requirements": {...}  # 分析需求
                }
            max_strategies: 最大策略数量
            min_compatibility_score: 最小兼容性分数
            
        Returns:
            List[ModuleStrategy]: 策略列表，按优先级排序
        """
        logger.info(f"开始生成策略，用户意图: {user_intent}")
        strategies = []
        
        # 确保模块已注册
        if not self.registered_modules:
            logger.info("模块未注册，开始自动发现模块")
            self.auto_discover_modules()
        
        logger.info(f"当前已注册模块: {list(self.registered_modules.keys())}")
        logger.info(f"可用数据库: {[db.get('name', 'Unknown') for db in self.available_databases]}")
        
        # 获取分析需求
        analysis_requirements = user_intent.get('analysis_requirements', {})
        required_modules = analysis_requirements.get('modules_needed', [])
        execution_order = analysis_requirements.get('execution_order', [])
        
        # 如果没有指定模块需求，使用默认的data_describe模块
        if not required_modules:
            required_modules = ['data_describe']
            execution_order = ['data_describe']
        
        logger.info(f"根据分析需求生成策略，需要的模块: {required_modules}")
        
        # 为每个需要的模块生成策略
        for i, module_id in enumerate(required_modules):
            if module_id not in self.registered_modules:
                logger.warning(f"模块 {module_id} 未注册，跳过")
                continue
                
            module_data = self.registered_modules[module_id]
            module_instance = module_data['instance']
            module_info = module_data['info']
            
            # 如果模块实例为None，进行延迟实例化
            if module_instance is None:
                try:
                    module_instance = self._instantiate_module(module_info)
                    self.registered_modules[module_id]['instance'] = module_instance
                    logger.info(f"延迟实例化模块: {module_id}")
                except Exception as e:
                    logger.error(f"实例化模块 {module_id} 失败: {e}")
                    continue
            
            # 遍历所有可用数据库
            for db_info in self.available_databases:
                logger.info(f"检查模块 {module_id} 与数据库 {db_info.get('name', 'Unknown')} 的兼容性")
                # 检查模块与数据库的兼容性
                compatibility = self._check_module_database_compatibility(
                    module_instance, db_info
                )
                logger.info(f"兼容性检查结果: {compatibility}")
                
                if compatibility['compatible'] and compatibility['score'] >= min_compatibility_score:
                    # 生成参数候选
                    parameter_candidates = self._generate_parameter_candidates(
                        module_info, user_intent, db_info
                    )
                    
                    for params in parameter_candidates:
                        # 计算策略优先级（考虑执行顺序）
                        base_priority = self._calculate_strategy_priority(
                            module_info, user_intent, compatibility, params
                        )
                        
                        # 根据执行顺序调整优先级
                        order_bonus = (len(execution_order) - i) * 10 if module_id in execution_order else 0
                        final_priority = base_priority + order_bonus
                        
                        # 创建策略
                        strategy = ModuleStrategy(
                            module_id=module_id,
                            module_name=module_info['module_name'],
                            module_instance=module_instance,
                            parameters=params,
                            database_info=db_info,
                            compatibility_score=compatibility['score'],
                            priority=final_priority,
                            estimated_execution_time=self._estimate_execution_time(
                                module_info, db_info, params
                            )
                        )
                        
                        strategies.append(strategy)
        
        # 按优先级排序并限制数量
        strategies.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"生成了 {len(strategies)} 个策略，返回前 {min(max_strategies, len(strategies))} 个")
        return strategies[:max_strategies]
    
    def _check_module_database_compatibility(self, 
                                           module_instance: Any, 
                                           db_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查模块与数据库的兼容性"""
        if module_instance is None:
            logger.error("模块实例为None，无法检查兼容性")
            return {
                'compatible': False,
                'score': 0.0,
                'reason': '模块实例为None'
            }
        
        db_type = db_info.get('type', '')
        available_fields = db_info.get('fields', [])
        
        try:
            return module_instance.check_database_compatibility(db_type, available_fields)
        except Exception as e:
            logger.error(f"检查模块兼容性时出错: {e}")
            return {
                'compatible': False,
                'score': 0.0,
                'reason': f'兼容性检查失败: {str(e)}'
            }
    
    def _generate_parameter_candidates(self, 
                                     module_info: Dict[str, Any],
                                     user_intent: Dict[str, Any],
                                     db_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成参数候选列表"""
        candidates = []
        
        # 基础参数
        base_params = {
            'data_source': db_info.get('path') or db_info.get('table_name', '')
        }
        
        # 从用户意图中提取参数
        intent_params = user_intent.get('parameters', {})
        base_params.update(intent_params)
        
        # 根据模块参数要求生成候选
        param_requirements = module_info.get('parameter_requirements', [])
        
        if not param_requirements:
            # 如果没有特殊要求，返回基础参数
            candidates.append(base_params)
        else:
            # 根据参数要求生成候选
            param_combinations = self._generate_parameter_combinations(
                param_requirements, base_params, user_intent
            )
            candidates.extend(param_combinations)
        
        return candidates if candidates else [base_params]
    
    def _generate_parameter_combinations(self, 
                                       param_requirements: List[Dict[str, Any]],
                                       base_params: Dict[str, Any],
                                       user_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成参数组合"""
        combinations = [base_params.copy()]
        
        for req in param_requirements:
            param_name = req['name']
            param_type = req['type']
            required = req.get('required', False)
            default_value = req.get('default_value')
            
            # 如果参数已在基础参数中，跳过
            if param_name in base_params:
                continue
            
            # 根据参数类型和用户意图生成值
            if required and param_name not in base_params:
                if default_value is not None:
                    for combo in combinations:
                        combo[param_name] = default_value
                elif param_type == 'boolean':
                    # 为布尔类型生成两种组合
                    new_combinations = []
                    for combo in combinations:
                        combo_true = combo.copy()
                        combo_true[param_name] = True
                        combo_false = combo.copy()
                        combo_false[param_name] = False
                        new_combinations.extend([combo_true, combo_false])
                    combinations = new_combinations
        
        return combinations
    
    def _calculate_strategy_priority(self, 
                                   module_info: Dict[str, Any],
                                   user_intent: Dict[str, Any],
                                   compatibility: Dict[str, Any],
                                   params: Dict[str, Any]) -> int:
        """计算策略优先级"""
        priority = 0
        
        # 兼容性分数权重 (0-50分)
        priority += int(compatibility['score'] * 50)
        
        # 意图匹配度 (0-30分)
        intent_match = self._calculate_intent_match(module_info, user_intent)
        priority += int(intent_match * 30)
        
        # 参数完整度 (0-20分)
        param_completeness = self._calculate_parameter_completeness(module_info, params)
        priority += int(param_completeness * 20)
        
        return priority
    
    def _calculate_intent_match(self, 
                              module_info: Dict[str, Any], 
                              user_intent: Dict[str, Any]) -> float:
        """计算意图匹配度"""
        # 简单的关键词匹配
        intent_target = user_intent.get('target', '').lower()
        module_name = module_info.get('module_name', '').lower()
        module_desc = module_info.get('description', '').lower()
        
        # 检查关键词匹配
        keywords = intent_target.split('_')
        match_score = 0.0
        
        for keyword in keywords:
            if keyword in module_name or keyword in module_desc:
                match_score += 1.0
        
        return min(match_score / max(len(keywords), 1), 1.0)
    
    def _calculate_parameter_completeness(self, 
                                        module_info: Dict[str, Any], 
                                        params: Dict[str, Any]) -> float:
        """计算参数完整度"""
        param_requirements = module_info.get('parameter_requirements', [])
        if not param_requirements:
            return 1.0
        
        required_params = [req for req in param_requirements if req.get('required', False)]
        if not required_params:
            return 1.0
        
        satisfied_count = sum(1 for req in required_params if req['name'] in params)
        return satisfied_count / len(required_params)
    
    def _estimate_execution_time(self, 
                               module_info: Dict[str, Any],
                               db_info: Dict[str, Any],
                               params: Dict[str, Any]) -> float:
        """估算执行时间（秒）"""
        # 基础时间
        base_time = 1.0
        
        # 根据数据库大小调整
        db_size = db_info.get('size', 0)
        if db_size > 1000000:  # 大于100万行
            base_time *= 3.0
        elif db_size > 100000:  # 大于10万行
            base_time *= 2.0
        
        # 根据模块复杂度调整
        complexity_indicators = [
            'visualization' in module_info.get('description', '').lower(),
            'machine_learning' in module_info.get('description', '').lower(),
            'statistical' in module_info.get('description', '').lower()
        ]
        complexity_multiplier = 1.0 + sum(complexity_indicators) * 0.5
        
        return base_time * complexity_multiplier
    
    def _instantiate_module(self, module_info: Dict[str, Any]) -> Any:
        """实例化模块"""
        try:
            # 支持两种配置格式：module_path 或 file_path
            module_path = module_info.get('module_path')
            file_path = module_info.get('file_path')
            class_name = module_info.get('class_name')
            
            if not class_name:
                raise ValueError(f"模块信息缺少class_name: {module_info}")
            
            # 如果有file_path，转换为module_path
            if file_path and not module_path:
                # 将文件路径转换为模块路径
                # 例如: modules/data_describe_module.py -> modules.data_describe_module
                module_path = file_path.replace('/', '.').replace('.py', '')
                logger.info(f"将file_path转换为module_path: {file_path} -> {module_path}")
            
            if not module_path:
                raise ValueError(f"模块信息不完整: module_path={module_path}, file_path={file_path}, class_name={class_name}")
            
            # 动态导入模块
            module = importlib.import_module(module_path)
            module_class = getattr(module, class_name)
            
            # 创建实例
            instance = module_class()
            logger.info(f"成功实例化模块: {module_path}.{class_name}")
            return instance
            
        except Exception as e:
            logger.error(f"实例化模块失败: {e}")
            raise
    
    def execute_strategy(self, strategy: ModuleStrategy) -> StrategyExecutionResult:
        """执行单个策略
        
        Args:
            strategy: 要执行的策略
            
        Returns:
            StrategyExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 准备数据上下文
            data_context = {
                'db_connector': strategy.database_info.get('connector'),
                'data_file': strategy.database_info.get('path'),
                'table_name': strategy.database_info.get('table_name'),
                'schema': strategy.database_info.get('fields')
            }
            
            # 执行模块
            result = strategy.module_instance.execute(
                strategy.parameters, 
                data_context
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 创建执行结果
            exec_result = StrategyExecutionResult(
                strategy=strategy,
                success=result.get('success', False),
                result=result,
                execution_time=execution_time,
                insights=result.get('insights', [])
            )
            
            # 记录执行历史
            self.execution_history.append(exec_result)
            
            logger.info(f"策略执行成功: {strategy.module_name} (耗时: {execution_time:.2f}s)")
            
            return exec_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            exec_result = StrategyExecutionResult(
                strategy=strategy,
                success=False,
                result={},
                execution_time=execution_time,
                error_message=str(e)
            )
            
            self.execution_history.append(exec_result)
            
            logger.error(f"策略执行失败: {strategy.module_name} - {e}")
            
            return exec_result
    
    def execute_strategies(self, strategies: List[ModuleStrategy]) -> List[StrategyExecutionResult]:
        """批量执行策略
        
        Args:
            strategies: 策略列表
            
        Returns:
            List[StrategyExecutionResult]: 执行结果列表
        """
        results = []
        
        for strategy in strategies:
            result = self.execute_strategy(strategy)
            results.append(result)
            
            # 如果执行失败，可以选择继续或停止
            if not result.success:
                logger.warning(f"策略 {strategy.module_name} 执行失败，继续执行下一个策略")
        
        return results
    
    def aggregate_results(self, results: List[StrategyExecutionResult]) -> Dict[str, Any]:
        """聚合多个策略的执行结果
        
        Args:
            results: 执行结果列表
            
        Returns:
            Dict[str, Any]: 聚合结果
        """
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        # 聚合洞察
        all_insights = []
        for result in successful_results:
            all_insights.extend(result.insights)
        
        # 聚合数据
        aggregated_data = []
        for result in successful_results:
            if 'data' in result.result:
                aggregated_data.extend(result.result['data'])
        
        # 计算总执行时间
        total_execution_time = sum(r.execution_time for r in results)
        
        return {
            'success': len(successful_results) > 0,
            'total_strategies': len(results),
            'successful_strategies': len(successful_results),
            'failed_strategies': len(failed_results),
            'aggregated_insights': all_insights,
            'aggregated_data': aggregated_data,
            'total_execution_time': total_execution_time,
            'individual_results': [{
                'strategy_name': r.strategy.module_name,
                'success': r.success,
                'execution_time': r.execution_time,
                'error': r.error_message
            } for r in results],
            'summary': self._generate_aggregated_summary(successful_results)
        }
    
    def _generate_aggregated_summary(self, successful_results: List[StrategyExecutionResult]) -> str:
        """生成聚合结果的总结"""
        if not successful_results:
            return "所有策略执行失败，无法生成分析结果。"
        
        summary_parts = [
            f"成功执行了 {len(successful_results)} 个分析策略。"
        ]
        
        # 添加各个模块的总结
        for result in successful_results:
            module_summary = result.result.get('summary', '')
            if module_summary:
                summary_parts.append(f"\n{result.strategy.module_name}: {module_summary}")
        
        # 添加综合洞察
        all_insights = []
        for result in successful_results:
            all_insights.extend(result.insights)
        
        if all_insights:
            unique_insights = list(set(all_insights))  # 去重
            summary_parts.append("\n综合洞察:")
            for insight in unique_insights[:5]:  # 最多显示5个洞察
                summary_parts.append(f"• {insight}")
        
        return " ".join(summary_parts)
    
    def generate_followup_strategies(self, 
                                   execution_results: List[StrategyExecutionResult],
                                   user_feedback: Dict[str, Any] = None) -> List[ModuleStrategy]:
        """根据执行结果生成后续策略
        
        Args:
            execution_results: 之前的执行结果
            user_feedback: 用户反馈
            
        Returns:
            List[ModuleStrategy]: 后续策略列表
        """
        followup_strategies = []
        
        # 分析执行结果，确定后续需求
        successful_results = [r for r in execution_results if r.success]
        
        if not successful_results:
            # 如果所有策略都失败了，建议重新配置或使用更基础的分析
            return self._generate_fallback_strategies()
        
        # 根据成功的结果生成后续分析建议
        for result in successful_results:
            # 检查结果中是否有可视化需求
            if 'visualization' in result.result and not result.result['visualization']:
                # 建议添加可视化策略
                viz_intent = {
                    'action': 'visualize',
                    'target': 'data_visualization',
                    'parameters': {
                        'data_source': result.strategy.parameters.get('data_source'),
                        'chart_types': ['histogram', 'scatter', 'correlation']
                    }
                }
                viz_strategies = self.generate_strategies(viz_intent, max_strategies=2)
                followup_strategies.extend(viz_strategies)
            
            # 检查是否需要更深入的分析
            insights = result.insights
            if any('缺失值' in insight for insight in insights):
                # 建议数据清洗策略
                cleaning_intent = {
                    'action': 'clean',
                    'target': 'data_cleaning',
                    'parameters': {
                        'data_source': result.strategy.parameters.get('data_source'),
                        'focus': 'missing_values'
                    }
                }
                cleaning_strategies = self.generate_strategies(cleaning_intent, max_strategies=1)
                followup_strategies.extend(cleaning_strategies)
        
        return followup_strategies
    
    def _generate_fallback_strategies(self) -> List[ModuleStrategy]:
        """生成备用策略"""
        # 生成最基础的数据描述策略
        basic_intent = {
            'action': 'analyze',
            'target': 'basic_description',
            'parameters': {}
        }
        
        return self.generate_strategies(basic_intent, max_strategies=1, min_compatibility_score=0.0)
    
    def get_execution_history(self) -> List[StrategyExecutionResult]:
        """获取执行历史"""
        return self.execution_history.copy()
    
    def clear_execution_history(self):
        """清空执行历史"""
        self.execution_history.clear()
        logger.info("执行历史已清空")
    
    def get_registered_modules_info(self) -> Dict[str, Any]:
        """获取已注册模块信息"""
        modules_info = {}
        for module_id, module_data in self.registered_modules.items():
            modules_info[module_id] = module_data['info']
        return modules_info
    
    def get_walker_status(self) -> Dict[str, Any]:
        """获取Walker状态信息"""
        return {
            'registered_modules_count': len(self.registered_modules),
            'available_databases_count': len(self.available_databases),
            'execution_history_count': len(self.execution_history),
            'modules_config_path': str(self.modules_config_path),
            'registered_modules': list(self.registered_modules.keys()),
            'available_database_types': [db.get('type') for db in self.available_databases]
        }
    
    def get_available_databases(self) -> List[str]:
        """
        获取可用的数据库列表
        
        Returns:
            可用数据库列表
        """
        return [db.get('name', f'db_{i}') for i, db in enumerate(self.available_databases)]
    
    def list_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有已注册的模块
        
        Returns:
            模块信息字典
        """
        return {module_id: module_data['info'] for module_id, module_data in self.registered_modules.items()}
    
    def generate_strategy(self, question: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据用户问题和意图生成策略
        
        Args:
            question: 用户问题
            intent: 意图信息
            
        Returns:
            生成的策略
        """
        try:
            # 分析用户意图
            intent_type = intent.get("intent", "general_chat")
            need_analysis = intent.get("need_data_analysis", False)
            
            if not need_analysis:
                return {
                    "strategies": [],
                    "reasoning": "不需要数据分析",
                    "confidence": 1.0
                }
            
            # 获取可用数据库
            available_dbs = self.get_available_databases()
            
            # 生成策略
            strategies = []
            
            # 对于数据分析意图，使用data_describe模块
            if intent_type in ["data_analysis", "data_query"] and "data_describe" in self.registered_modules:
                for i, db_info in enumerate(self.available_databases):
                    strategy = {
                        "module_id": "data_describe",
                        "parameters": {
                            "data_path": db_info.get("path", "data"),
                            "file_types": ["csv", "parquet", "duckdb"]
                        },
                        "database_info": db_info,
                        "priority": 1,
                        "reasoning": f"分析{db_info.get('name', f'数据库{i}')}中的数据"
                    }
                    strategies.append(strategy)
            
            return {
                "strategies": strategies,
                "reasoning": f"为{intent_type}意图生成了{len(strategies)}个策略",
                "confidence": 0.8 if strategies else 0.1
            }
            
        except Exception as e:
            logger.error(f"策略生成失败: {e}")
            return {
                "strategies": [],
                "reasoning": f"策略生成失败: {e}",
                "confidence": 0.0
            }


# 全局Walker实例
_global_walker = None


def get_walker() -> Walker:
    """获取全局Walker实例"""
    global _global_walker
    if _global_walker is None:
        _global_walker = Walker()
    return _global_walker


def reset_walker():
    """重置全局Walker实例"""
    global _global_walker
    _global_walker = None