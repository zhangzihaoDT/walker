#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块执行器 - 负责执行具体的分析模块

与Walker配合工作，提供模块执行的具体实现
"""

import os
import json
import importlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ModuleExecutor:
    """模块执行器
    
    负责加载、实例化和执行分析模块
    """
    
    def __init__(self, modules_dir: str = None):
        """初始化模块执行器
        
        Args:
            modules_dir: 模块目录路径
        """
        if modules_dir is None:
            project_root = Path(__file__).parent.parent
            modules_dir = project_root / "modules"
        
        self.modules_dir = Path(modules_dir)
        self.loaded_modules = {}
        self.module_instances = {}
    
    def load_module_from_config(self, module_config: Dict[str, Any]) -> Optional[Any]:
        """从配置加载模块
        
        Args:
            module_config: 模块配置字典
            
        Returns:
            模块类或None
        """
        try:
            file_path = module_config.get('file_path', '')
            class_name = module_config.get('class_name', '')
            
            if not file_path or not class_name:
                logger.error(f"模块配置不完整: {module_config}")
                return None
            
            # 转换文件路径为模块路径
            module_path = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            
            # 动态导入模块
            module = importlib.import_module(module_path)
            
            # 获取模块类
            if hasattr(module, class_name):
                module_class = getattr(module, class_name)
                self.loaded_modules[module_config['module_id']] = module_class
                logger.info(f"成功加载模块: {module_config['module_id']}")
                return module_class
            else:
                logger.error(f"模块 {module_path} 中未找到类 {class_name}")
                return None
                
        except ImportError as e:
            logger.error(f"导入模块失败 {module_config.get('file_path', '')}: {e}")
            return None
        except Exception as e:
            logger.error(f"加载模块失败 {module_config.get('module_id', '')}: {e}")
            return None
    
    def get_module_instance(self, module_id: str, module_config: Dict[str, Any] = None) -> Optional[Any]:
        """获取模块实例
        
        Args:
            module_id: 模块ID
            module_config: 模块配置（如果模块未加载）
            
        Returns:
            模块实例或None
        """
        # 如果实例已存在，直接返回
        if module_id in self.module_instances:
            return self.module_instances[module_id]
        
        # 如果模块类已加载，创建实例
        if module_id in self.loaded_modules:
            try:
                module_class = self.loaded_modules[module_id]
                instance = module_class()
                self.module_instances[module_id] = instance
                return instance
            except Exception as e:
                logger.error(f"创建模块实例失败 {module_id}: {e}")
                return None
        
        # 如果模块未加载，尝试从配置加载
        if module_config:
            module_class = self.load_module_from_config(module_config)
            if module_class:
                try:
                    instance = module_class()
                    self.module_instances[module_id] = instance
                    return instance
                except Exception as e:
                    logger.error(f"创建模块实例失败 {module_id}: {e}")
                    return None
        
        logger.error(f"无法获取模块实例: {module_id}")
        return None
    
    def execute_module(self, 
                      module_id: str, 
                      parameters: Dict[str, Any],
                      data_context: Dict[str, Any] = None,
                      module_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行模块
        
        Args:
            module_id: 模块ID
            parameters: 执行参数
            data_context: 数据上下文
            module_config: 模块配置
            
        Returns:
            执行结果
        """
        try:
            # 获取模块实例
            instance = self.get_module_instance(module_id, module_config)
            if not instance:
                return {
                    "success": False,
                    "error": f"无法获取模块实例: {module_id}",
                    "module": module_id
                }
            
            # 验证参数
            validation_result = instance.validate_parameters(parameters)
            if not validation_result.get('valid', True):
                return {
                    "success": False,
                    "error": f"参数验证失败: {validation_result.get('error', '未知错误')}",
                    "module": module_id,
                    "parameters": parameters
                }
            
            # 执行模块
            result = instance.execute(parameters, data_context)
            
            logger.info(f"模块执行成功: {module_id}")
            return result
            
        except Exception as e:
            logger.error(f"模块执行失败 {module_id}: {e}")
            return {
                "success": False,
                "error": f"模块执行异常: {str(e)}",
                "module": module_id,
                "parameters": parameters
            }
    
    def batch_execute_modules(self, 
                             execution_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量执行模块
        
        Args:
            execution_plans: 执行计划列表
            [
                {
                    "module_id": "data_describe",
                    "parameters": {...},
                    "data_context": {...},
                    "module_config": {...}
                },
                ...
            ]
            
        Returns:
            执行结果列表
        """
        results = []
        
        for plan in execution_plans:
            module_id = plan.get('module_id')
            parameters = plan.get('parameters', {})
            data_context = plan.get('data_context', {})
            module_config = plan.get('module_config', {})
            
            result = self.execute_module(
                module_id, parameters, data_context, module_config
            )
            results.append(result)
        
        return results
    
    def get_module_info(self, module_id: str) -> Optional[Dict[str, Any]]:
        """获取模块信息
        
        Args:
            module_id: 模块ID
            
        Returns:
            模块信息字典或None
        """
        instance = self.get_module_instance(module_id)
        if instance:
            return instance.get_module_info()
        return None
    
    def list_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用模块
        
        Returns:
            模块信息字典
        """
        modules_info = {}
        
        for module_id in self.loaded_modules.keys():
            info = self.get_module_info(module_id)
            if info:
                modules_info[module_id] = info
        
        return modules_info
    
    def list_modules(self) -> List[str]:
        """
        列出所有可用的模块ID
        
        Returns:
            模块ID列表
        """
        return list(self.loaded_modules.keys())
    
    def clear_instances(self):
        """清空所有模块实例"""
        self.module_instances.clear()
        logger.info("已清空所有模块实例")
    
    def reload_module(self, module_id: str, module_config: Dict[str, Any]):
        """重新加载模块
        
        Args:
            module_id: 模块ID
            module_config: 模块配置
        """
        # 清除现有实例和类
        if module_id in self.module_instances:
            del self.module_instances[module_id]
        if module_id in self.loaded_modules:
            del self.loaded_modules[module_id]
        
        # 重新加载
        self.load_module_from_config(module_config)
        logger.info(f"模块 {module_id} 已重新加载")
    
    def create_execution_plan(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据Walker策略创建执行计划
        
        Args:
            strategy: Walker生成的策略
            
        Returns:
            执行计划列表
        """
        execution_plan = []
        
        try:
            strategies = strategy.get("strategies", [])
            
            for i, strat in enumerate(strategies):
                module_id = strat.get("module_id")
                parameters = strat.get("parameters", {})
                database_info = strat.get("database_info", {})
                
                if module_id in self.loaded_modules:
                    execution_plan.append({
                        "step_id": i + 1,
                        "module_id": module_id,
                        "parameters": parameters,
                        "database_info": database_info,
                        "priority": strat.get("priority", 1)
                    })
                    
            # 按优先级排序
            execution_plan.sort(key=lambda x: x.get("priority", 1))
            
        except Exception as e:
            logger.error(f"创建执行计划失败: {e}")
            
        return execution_plan
    
    def execute_plan(self, execution_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行执行计划
        
        Args:
            execution_plan: 执行计划列表
            
        Returns:
            执行结果列表
        """
        results = []
        
        for step in execution_plan:
            try:
                module_id = step["module_id"]
                parameters = step["parameters"]
                database_info = step["database_info"]
                
                # 执行模块
                result = self.execute_module(
                    module_id=module_id,
                    parameters=parameters,
                    data_context=database_info
                )
                
                results.append({
                    "step_id": step["step_id"],
                    "module_id": module_id,
                    "success": result.get("success", False),
                    "output": result.get("result", ""),
                    "error": result.get("error"),
                    "metadata": result.get("metadata", {})
                })
                
            except Exception as e:
                logger.error(f"执行步骤 {step.get('step_id')} 失败: {e}")
                results.append({
                    "step_id": step.get("step_id"),
                    "module_id": step.get("module_id"),
                    "success": False,
                    "output": "",
                    "error": str(e),
                    "metadata": {}
                })
                
        return results


# 全局模块执行器实例
_global_executor = None


def get_module_executor() -> ModuleExecutor:
    """获取全局模块执行器实例"""
    global _global_executor
    if _global_executor is None:
        _global_executor = ModuleExecutor()
    return _global_executor


def reset_module_executor():
    """重置全局模块执行器实例"""
    global _global_executor
    _global_executor = None