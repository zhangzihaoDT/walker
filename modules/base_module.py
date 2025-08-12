"""分析模块基类

定义所有分析模块的统一接口和标准。
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime


class BaseAnalysisModule(ABC):
    """分析模块基类
    
    所有分析模块都应继承此类，实现统一的接口标准。
    这样可以确保模块间的一致性，便于系统调度和管理。
    
    新增数据库感知能力：
    - 声明支持的数据库类型
    - 声明所需的数据字段
    - 提供数据准备接口
    """
    
    # 模块基本信息
    module_id: str = "base_module"
    module_name: str = "基础分析模块"
    description: str = "所有分析模块的基类，定义统一接口"
    
    # 数据库感知能力
    supported_databases: List[str] = []  # 支持的数据库类型，如 ['duckdb', 'sqlite', 'csv']
    required_fields: List[str] = []      # 模块需要的数据字段
    optional_fields: List[str] = []      # 可选的数据字段
    
    def __init__(self):
        """初始化模块"""
        pass
    
    @abstractmethod
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> Any:
        """根据数据库连接器和参数准备数据
        
        Args:
            db_connector: 数据库连接器对象
            params: 分析参数字典
                
        Returns:
            Any: 准备好的数据对象（DataFrame、查询结果等）
        """
        raise NotImplementedError("子类必须实现prepare_data方法")
    
    @abstractmethod
    def run(self, data: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析逻辑
        
        Args:
            data: 准备好的数据
            params: 分析参数字典
                
        Returns:
            Dict[str, Any]: 分析结果
        """
        raise NotImplementedError("子类必须实现run方法")
    
    @abstractmethod
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成分析结果的文字解读
        
        Args:
            results: 分析结果字典
                
        Returns:
            str: 文字解读
        """
        raise NotImplementedError("子类必须实现summarize方法")
    
    def execute(self, parameters: Dict[str, Any], data_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行分析模块的核心逻辑（兼容旧接口）
        
        这是一个兼容性方法，内部会调用新的三步式流程：
        1. prepare_data - 准备数据
        2. run - 执行分析
        3. summarize - 生成总结
        
        Args:
            parameters: 分析参数字典
                - 包含模块执行所需的所有参数
                - 参数名和类型由具体模块定义
            data_context: 数据上下文字典
                - data_file: 数据文件路径
                - db_path: 数据库路径（可选）
                - db_connector: 数据库连接器
                - table_name: 表名
                - schema: 数据schema信息
                
        Returns:
            Dict[str, Any]: 标准化的分析结果
            {
                "success": bool,           # 执行是否成功
                "module": str,             # 模块名称
                "parameters": dict,        # 使用的参数
                "data": list,              # 结果数据（可序列化格式）
                "analysis": dict,          # 分析结果统计
                "visualization": dict,     # 可视化配置
                "insights": list,          # 分析洞察
                "summary": str,            # 文本总结
                "timestamp": str,          # 执行时间戳
                "error": str               # 错误信息（如果失败）
            }
        """
        try:
            # 获取数据库连接器
            db_connector = data_context.get('db_connector') if data_context else None
            
            # 三步式执行流程
            data = self.prepare_data(db_connector, parameters)
            results = self.run(data, parameters)
            summary = self.summarize(results)
            
            # 构建标准化结果
            return {
                "success": True,
                "module": self.module_name,
                "parameters": parameters,
                "data": self._convert_to_serializable(results.get('data', [])),
                "analysis": results.get('analysis', {}),
                "visualization": results.get('visualization', {}),
                "insights": results.get('insights', []),
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return self._handle_error(e, parameters)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证输入参数
        
        Args:
            parameters: 待验证的参数字典
            
        Returns:
            Dict[str, Any]: 验证结果
            {
                "valid": bool,     # 是否有效
                "error": str       # 错误信息（如果无效）
            }
        """
        # 基类提供默认实现，子类可以重写
        return {"valid": True}
    
    def get_parameter_requirements(self) -> List[Any]:
        """获取参数要求列表
        
        Returns:
            List[ParameterRequirement]: 参数要求列表
        """
        return getattr(self, 'parameter_requirements', [])
    
    def check_database_compatibility(self, database_type: str, available_fields: List[str]) -> Dict[str, Any]:
        """检查与指定数据库的兼容性
        
        Args:
            database_type: 数据库类型
            available_fields: 数据库中可用的字段列表
            
        Returns:
            Dict[str, Any]: 兼容性检查结果
            {
                "compatible": bool,        # 是否兼容
                "missing_fields": list,    # 缺失的必需字段
                "available_fields": list,  # 可用的可选字段
                "score": float            # 兼容性评分 (0-1)
            }
        """
        # 检查数据库类型支持
        if self.supported_databases and database_type not in self.supported_databases:
            return {
                "compatible": False,
                "missing_fields": self.required_fields,
                "available_fields": [],
                "score": 0.0,
                "reason": f"不支持数据库类型: {database_type}"
            }
        
        # 检查必需字段
        missing_fields = [field for field in self.required_fields if field not in available_fields]
        
        # 检查可选字段
        available_optional = [field for field in self.optional_fields if field in available_fields]
        
        # 计算兼容性评分
        if missing_fields:
            compatible = False
            score = 0.0
        else:
            compatible = True
            # 基础分 0.5，可选字段每个加分
            base_score = 0.5
            optional_score = 0.5 * (len(available_optional) / max(len(self.optional_fields), 1)) if self.optional_fields else 0.5
            score = base_score + optional_score
        
        return {
            "compatible": compatible,
            "missing_fields": missing_fields,
            "available_fields": available_optional,
            "score": min(score, 1.0)
        }
    
    def get_data_requirements(self) -> Dict[str, Any]:
        """获取数据需求信息
        
        Returns:
            Dict[str, Any]: 数据需求信息
        """
        return {
            "supported_databases": self.supported_databases,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "description": f"{self.module_name}的数据需求"
        }
    
    def get_module_info(self) -> Dict[str, Any]:
        """获取模块信息
        
        Returns:
            Dict[str, Any]: 模块信息
        """
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "description": self.description,
            "class_name": self.__class__.__name__,
            "supported_databases": self.supported_databases,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "parameter_requirements": [
                {
                    "name": req.name,
                    "type": req.param_type.value,
                    "required": req.required,
                    "description": req.description,
                    "valid_values": req.valid_values,
                    "default_value": req.default_value,
                    "example": req.example
                }
                for req in self.get_parameter_requirements()
            ]
        }
    
    def _handle_error(self, error: Exception, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """统一的错误处理
        
        Args:
            error: 异常对象
            parameters: 执行参数
            
        Returns:
            Dict[str, Any]: 错误结果
        """
        return {
            "success": False,
            "error": f"{self.module_name}执行失败: {str(error)}",
            "module": self.module_name,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
    
    def _convert_to_serializable(self, data: Any) -> Any:
        """转换数据为可序列化格式
        
        Args:
            data: 待转换的数据
            
        Returns:
            Any: 可序列化的数据
        """
        import pandas as pd
        
        if isinstance(data, pd.DataFrame):
            # 转换DataFrame为字典列表
            records = data.to_dict('records')
            # 处理numpy类型
            for record in records:
                for key, value in record.items():
                    if hasattr(value, 'item'):  # numpy类型
                        record[key] = value.item()
                    elif pd.isna(value):
                        record[key] = None
            return records
        elif isinstance(data, dict):
            # 递归处理字典
            return {k: self._convert_to_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            # 递归处理列表
            return [self._convert_to_serializable(item) for item in data]
        elif hasattr(data, 'item'):  # numpy类型
            return data.item()
        elif pd.isna(data) if 'pd' in locals() else False:
            return None
        else:
            return data