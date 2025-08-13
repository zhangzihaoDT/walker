#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库Schema自动扫描器

自动扫描data/目录下的所有数据文件，提取表结构信息
支持CSV、Parquet、DuckDB等格式
返回结构化的schema字典
"""

import os
import pandas as pd
import duckdb
from pathlib import Path
from typing import Dict, Any, List, Union
import warnings
warnings.filterwarnings('ignore')


class DatabaseSchemaScanner:
    """数据库Schema扫描器"""
    
    def __init__(self, data_dir: str = None):
        """初始化Schema扫描器
        
        Args:
            data_dir: 数据目录路径，默认为项目根目录下的data文件夹
        """
        if data_dir is None:
            # 获取当前脚本所在目录的上级目录，然后拼接data路径
            current_dir = Path(__file__).parent.parent
            self.data_dir = current_dir / "data"
        else:
            self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"数据目录不存在: {self.data_dir}")
    
    def get_data_files(self) -> List[Path]:
        """获取数据目录下所有支持的数据文件
        
        Returns:
            支持的数据文件路径列表
        """
        supported_extensions = {'.csv', '.parquet', '.duckdb', '.db'}
        data_files = []
        
        for file_path in self.data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                data_files.append(file_path)
        
        return sorted(data_files)
    
    def get_dataframe_schema(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """获取DataFrame的schema信息
        
        Args:
            df: pandas DataFrame
            table_name: 表名
            
        Returns:
            表的schema信息字典
        """
        if df is None or df.empty:
            return {
                "table_name": table_name,
                "row_count": 0,
                "column_count": 0,
                "columns": {},
                "error": "数据为空或无效"
            }
        
        # 构建列信息
        columns_info = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # 转换pandas数据类型为更通用的类型
            if 'int' in dtype:
                data_type = 'INTEGER'
            elif 'float' in dtype:
                data_type = 'FLOAT'
            elif 'bool' in dtype:
                data_type = 'BOOLEAN'
            elif 'datetime' in dtype:
                data_type = 'DATETIME'
            elif 'object' in dtype or 'string' in dtype:
                data_type = 'TEXT'
            else:
                data_type = dtype.upper()
            
            # 处理sample_values，确保JSON可序列化
            sample_values = []
            try:
                samples = df[col].dropna().head(3)
                for val in samples:
                    if pd.isna(val):
                        sample_values.append(None)
                    elif hasattr(val, 'isoformat'):  # datetime类型
                        sample_values.append(val.isoformat())
                    elif hasattr(val, 'item'):  # numpy类型
                        sample_values.append(val.item())
                    else:
                        sample_values.append(str(val))
            except Exception:
                sample_values = []
            
            columns_info[col] = {
                "data_type": data_type,
                "pandas_dtype": dtype,
                "nullable": bool(df[col].isnull().any()),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
                "sample_values": sample_values
            }
        
        return {
            "table_name": table_name,
            "row_count": int(df.shape[0]),
            "column_count": int(df.shape[1]),
            "columns": columns_info,
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
    
    def scan_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """扫描CSV文件的schema
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            文件的schema信息
        """
        try:
            # 尝试不同的编码格式读取CSV
            encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'gbk', 'gb2312', 'gb18030']
            separators = [',', '\t', ';', '|']
            
            df = None
            for encoding in encodings:
                for sep in separators:
                    try:
                        df_sample = pd.read_csv(file_path, encoding=encoding, sep=sep, nrows=1000)  # 只读取前1000行用于schema分析
                        if df_sample.shape[1] > 1 or (df_sample.shape[1] == 1 and not df_sample.columns[0].startswith('ÿþ') and '\t' not in df_sample.columns[0]):
                            # 读取完整文件获取准确的行数
                            df_full = pd.read_csv(file_path, encoding=encoding, sep=sep)
                            df = df_full
                            break
                    except Exception:
                        continue
                if df is not None:
                    break
            
            if df is None:
                return {
                    "file_name": file_path.name,
                    "file_type": "CSV",
                    "tables": {},
                    "error": "无法读取CSV文件"
                }
            
            table_name = file_path.stem  # 使用文件名（不含扩展名）作为表名
            schema_info = self.get_dataframe_schema(df_full, table_name)
            
            return {
                "file_name": file_path.name,
                "file_type": "CSV",
                "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "tables": {table_name: schema_info}
            }
            
        except Exception as e:
            return {
                "file_name": file_path.name,
                "file_type": "CSV",
                "tables": {},
                "error": f"扫描CSV文件失败: {str(e)}"
            }
    
    def scan_parquet_file(self, file_path: Path) -> Dict[str, Any]:
        """扫描Parquet文件的schema
        
        Args:
            file_path: Parquet文件路径
            
        Returns:
            文件的schema信息
        """
        try:
            df = pd.read_parquet(file_path)
            table_name = file_path.stem
            schema_info = self.get_dataframe_schema(df, table_name)
            
            return {
                "file_name": file_path.name,
                "file_type": "PARQUET",
                "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "tables": {table_name: schema_info}
            }
            
        except Exception as e:
            return {
                "file_name": file_path.name,
                "file_type": "PARQUET",
                "tables": {},
                "error": f"扫描Parquet文件失败: {str(e)}"
            }
    
    def scan_duckdb_file(self, file_path: Path) -> Dict[str, Any]:
        """扫描DuckDB文件的schema
        
        Args:
            file_path: DuckDB文件路径
            
        Returns:
            文件的schema信息
        """
        try:
            conn = duckdb.connect(str(file_path))
            
            # 获取所有表名
            tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            tables_result = conn.execute(tables_query).fetchall()
            table_names = [row[0] for row in tables_result]
            
            if not table_names:
                conn.close()
                return {
                    "file_name": file_path.name,
                    "file_type": "DUCKDB",
                    "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                    "tables": {},
                    "error": "DuckDB文件中没有找到表"
                }
            
            tables_schema = {}
            for table_name in table_names:
                try:
                    # 获取表的详细schema信息
                    schema_query = f"DESCRIBE {table_name}"
                    schema_result = conn.execute(schema_query).fetchall()
                    
                    # 获取表数据用于统计信息
                    df = conn.execute(f"SELECT * FROM {table_name}").df()
                    
                    # 构建列信息（结合DuckDB的schema信息和pandas分析）
                    columns_info = {}
                    for row in schema_result:
                        col_name = row[0]
                        col_type = row[1]
                        col_nullable = row[2] == 'YES'
                        
                        # 从DataFrame获取统计信息
                        if col_name in df.columns:
                            null_count = int(df[col_name].isnull().sum())
                            unique_count = int(df[col_name].nunique())
                            
                            # 处理sample_values，确保JSON可序列化
                            sample_values = []
                            try:
                                samples = df[col_name].dropna().head(3)
                                for val in samples:
                                    if pd.isna(val):
                                        sample_values.append(None)
                                    elif hasattr(val, 'isoformat'):  # datetime类型
                                        sample_values.append(val.isoformat())
                                    elif hasattr(val, 'item'):  # numpy类型
                                        sample_values.append(val.item())
                                    else:
                                        sample_values.append(str(val))
                            except Exception:
                                sample_values = []
                        else:
                            null_count = 0
                            unique_count = 0
                            sample_values = []
                        
                        columns_info[col_name] = {
                            "data_type": col_type,
                            "nullable": col_nullable,
                            "null_count": null_count,
                            "unique_count": unique_count,
                            "sample_values": sample_values
                        }
                    
                    tables_schema[table_name] = {
                        "table_name": table_name,
                        "row_count": int(df.shape[0]),
                        "column_count": int(df.shape[1]),
                        "columns": columns_info,
                        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
                    }
                    
                except Exception as e:
                    tables_schema[table_name] = {
                        "table_name": table_name,
                        "error": f"扫描表失败: {str(e)}"
                    }
            
            conn.close()
            
            return {
                "file_name": file_path.name,
                "file_type": "DUCKDB",
                "file_size_mb": round(file_path.stat().st_size / 1024 / 1024, 2),
                "tables": tables_schema
            }
            
        except Exception as e:
            return {
                "file_name": file_path.name,
                "file_type": "DUCKDB",
                "tables": {},
                "error": f"连接DuckDB文件失败: {str(e)}"
            }
    
    def scan_all_databases(self) -> Dict[str, Any]:
        """扫描所有数据库文件的schema
        
        Returns:
            完整的数据库schema字典
        """
        print(f"🔍 开始扫描数据目录: {self.data_dir}")
        
        data_files = self.get_data_files()
        if not data_files:
            return {
                "scan_summary": {
                    "total_files": 0,
                    "total_tables": 0,
                    "scan_status": "没有找到支持的数据文件"
                },
                "databases": {}
            }
        
        print(f"📁 找到 {len(data_files)} 个数据文件")
        
        databases_schema = {}
        total_tables = 0
        
        for file_path in data_files:
            print(f"\n🔄 扫描文件: {file_path.name}")
            
            if file_path.suffix.lower() == '.csv':
                schema_info = self.scan_csv_file(file_path)
            elif file_path.suffix.lower() == '.parquet':
                schema_info = self.scan_parquet_file(file_path)
            elif file_path.suffix.lower() in ['.duckdb', '.db']:
                schema_info = self.scan_duckdb_file(file_path)
            else:
                continue
            
            databases_schema[file_path.name] = schema_info
            
            # 统计表数量
            if 'tables' in schema_info and isinstance(schema_info['tables'], dict):
                total_tables += len(schema_info['tables'])
                print(f"✓ 扫描完成: {len(schema_info['tables'])} 个表")
            else:
                print(f"⚠ 扫描失败或无表")
        
        # 构建完整的schema结果
        result = {
            "scan_summary": {
                "total_files": len(data_files),
                "total_tables": total_tables,
                "scan_status": "扫描完成",
                "data_directory": str(self.data_dir)
            },
            "databases": databases_schema
        }
        
        print(f"\n🎉 Schema扫描完成！共扫描 {len(data_files)} 个文件，{total_tables} 个表")
        return result
    
    def print_schema_summary(self, schema_dict: Dict[str, Any]):
        """打印schema摘要信息
        
        Args:
            schema_dict: scan_all_databases返回的schema字典
        """
        print("\n" + "="*80)
        print("📊 数据库Schema扫描结果摘要")
        print("="*80)
        
        summary = schema_dict.get('scan_summary', {})
        print(f"📁 扫描目录: {summary.get('data_directory', 'Unknown')}")
        print(f"📄 文件总数: {summary.get('total_files', 0)}")
        print(f"🗃️  表总数: {summary.get('total_tables', 0)}")
        print(f"📊 扫描状态: {summary.get('scan_status', 'Unknown')}")
        
        databases = schema_dict.get('databases', {})
        
        for file_name, db_info in databases.items():
            print(f"\n📋 文件: {file_name} ({db_info.get('file_type', 'Unknown')})")
            print(f"   大小: {db_info.get('file_size_mb', 0)} MB")
            
            if 'error' in db_info:
                print(f"   ❌ 错误: {db_info['error']}")
                continue
            
            tables = db_info.get('tables', {})
            print(f"   表数量: {len(tables)}")
            
            for table_name, table_info in tables.items():
                if 'error' in table_info:
                    print(f"     ❌ 表 {table_name}: {table_info['error']}")
                    continue
                
                print(f"     📊 表 {table_name}:")
                print(f"        行数: {table_info.get('row_count', 0):,}")
                print(f"        列数: {table_info.get('column_count', 0)}")
                print(f"        内存: {table_info.get('memory_usage_mb', 0)} MB")
                
                # 显示前几个列的信息
                columns = table_info.get('columns', {})
                if columns:
                    print(f"        主要字段:")
                    for i, (col_name, col_info) in enumerate(list(columns.items())[:5]):
                        data_type = col_info.get('data_type', 'Unknown')
                        nullable = "可空" if col_info.get('nullable', False) else "非空"
                        print(f"          {col_name}: {data_type} ({nullable})")
                    
                    if len(columns) > 5:
                        print(f"          ... 还有 {len(columns) - 5} 个字段")
    
    def export_schema_to_json(self, schema_dict: Dict[str, Any], output_file: str = "database_schema.json"):
        """导出schema到JSON文件
        
        Args:
            schema_dict: schema字典
            output_file: 输出文件名
        """
        import json
        
        try:
            # 确保输出到当前脚本所在的prepare目录
            output_path = Path(__file__).parent / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(schema_dict, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Schema已导出到: {output_path}")
        except Exception as e:
            print(f"\n❌ 导出失败: {str(e)}")


def main():
    """主函数 - 演示如何使用Schema扫描器"""
    try:
        # 创建扫描器实例
        scanner = DatabaseSchemaScanner()
        
        # 扫描所有数据库
        schema_result = scanner.scan_all_databases()
        
        # 打印摘要信息
        scanner.print_schema_summary(schema_result)
        
        # 导出到JSON文件
        scanner.export_schema_to_json(schema_result)
        
        return schema_result
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        return None


if __name__ == "__main__":
    main()