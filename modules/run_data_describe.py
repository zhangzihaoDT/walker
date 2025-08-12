#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析器 - 自动读取并分析data目录下的所有数据文件
支持的文件格式：CSV, Parquet, DuckDB
"""

import os
import pandas as pd
import duckdb
from pathlib import Path
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')


class DataAnalyzer:
    """数据分析器类，用于自动读取和分析各种格式的数据文件"""
    
    def __init__(self, data_dir: str = None):
        """初始化数据分析器
        
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
    
    def read_csv_file(self, file_path: Path) -> pd.DataFrame:
        """读取CSV文件"""
        try:
            # 尝试不同的编码格式和分隔符
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'utf-16']
            separators = [',', '\t', ';', '|']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                        # 如果只有一列但包含制表符，直接尝试制表符分隔
                        if df.shape[1] == 1 and '\t' in df.columns[0]:
                            try:
                                df_tab = pd.read_csv(file_path, encoding=encoding, sep='\t')
                                if df_tab.shape[1] > 1:
                                    print(f"✓ 成功读取CSV文件 (编码: {encoding}, 分隔符: '\t'): {file_path.name}")
                                    return df_tab
                            except Exception:
                                pass
                        # 检查是否成功解析（列数大于1或者有合理的数据）
                        if df.shape[1] > 1 or (df.shape[1] == 1 and not df.columns[0].startswith('ÿþ') and '\t' not in df.columns[0]):
                            print(f"✓ 成功读取CSV文件 (编码: {encoding}, 分隔符: '{sep}'): {file_path.name}")
                            return df
                    except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError):
                        continue
            
            # 如果所有编码都失败，尝试使用latin-1编码
            try:
                df = pd.read_csv(file_path, encoding='latin-1', sep='\t')
                print(f"⚠ 使用latin-1编码读取CSV文件: {file_path.name}")
                return df
            except Exception:
                print(f"✗ 所有编码格式都无法读取CSV文件: {file_path.name}")
                return None
            
        except Exception as e:
            print(f"✗ 读取CSV文件失败: {file_path.name}, 错误: {e}")
            return None
    
    def read_parquet_file(self, file_path: Path) -> pd.DataFrame:
        """读取Parquet文件"""
        try:
            df = pd.read_parquet(file_path)
            print(f"✓ 成功读取Parquet文件: {file_path.name}")
            return df
        except Exception as e:
            print(f"✗ 读取Parquet文件失败: {file_path.name}, 错误: {e}")
            return None
    
    def read_duckdb_file(self, file_path: Path) -> Dict[str, pd.DataFrame]:
        """读取DuckDB文件中的所有表"""
        try:
            conn = duckdb.connect(str(file_path))
            
            # 获取所有表名
            tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            tables_result = conn.execute(tables_query).fetchall()
            table_names = [row[0] for row in tables_result]
            
            if not table_names:
                print(f"⚠ DuckDB文件中没有找到表: {file_path.name}")
                conn.close()
                return {}
            
            tables_data = {}
            for table_name in table_names:
                try:
                    df = conn.execute(f"SELECT * FROM {table_name}").df()
                    tables_data[table_name] = df
                    print(f"✓ 成功读取DuckDB表: {file_path.name}.{table_name}")
                except Exception as e:
                    print(f"✗ 读取DuckDB表失败: {file_path.name}.{table_name}, 错误: {e}")
            
            conn.close()
            return tables_data
            
        except Exception as e:
            print(f"✗ 连接DuckDB文件失败: {file_path.name}, 错误: {e}")
            return {}
    
    def describe_dataframe(self, df: pd.DataFrame, name: str) -> Dict[str, Any]:
        """对DataFrame进行基本描述统计
        
        Args:
            df: 要分析的DataFrame
            name: 数据集名称
            
        Returns:
            包含描述统计信息的字典
        """
        if df is None or df.empty:
            return {"error": "数据为空或无效"}
        
        description = {
            "数据集名称": name,
            "数据形状": df.shape,
            "行数": df.shape[0],
            "列数": df.shape[1],
            "列名": list(df.columns),
            "数据类型": df.dtypes.to_dict(),
            "缺失值统计": df.isnull().sum().to_dict(),
            "内存使用": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }
        
        # 数值列的描述统计
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            description["数值列描述统计"] = df[numeric_cols].describe().to_dict()
        
        # 文本列的基本信息
        text_cols = df.select_dtypes(include=['object', 'string']).columns
        if len(text_cols) > 0:
            text_info = {}
            for col in text_cols:
                text_info[col] = {
                    "唯一值数量": df[col].nunique(),
                    "最常见值": df[col].mode().iloc[0] if not df[col].mode().empty else None
                }
            description["文本列信息"] = text_info
        
        return description
    
    def print_description(self, description: Dict[str, Any]):
        """格式化打印数据描述信息"""
        print("\n" + "="*60)
        print(f"📊 数据集: {description.get('数据集名称', 'Unknown')}")
        print("="*60)
        
        if "error" in description:
            print(f"❌ 错误: {description['error']}")
            return
        
        print(f"📏 数据形状: {description['数据形状']} (行数: {description['行数']}, 列数: {description['列数']})")
        print(f"💾 内存使用: {description['内存使用']}")
        
        print("\n📋 列信息:")
        for i, (col, dtype) in enumerate(description['数据类型'].items(), 1):
            missing = description['缺失值统计'].get(col, 0)
            missing_pct = (missing / description['行数'] * 100) if description['行数'] > 0 else 0
            print(f"  {i:2d}. {col:<20} | 类型: {str(dtype):<10} | 缺失: {missing:>6} ({missing_pct:5.1f}%)")
        
        # 数值列统计
        if "数值列描述统计" in description:
            print("\n📈 数值列统计:")
            numeric_stats = description["数值列描述统计"]
            for col in numeric_stats:
                stats = numeric_stats[col]
                print(f"  {col}:")
                print(f"    均值: {stats.get('mean', 'N/A'):>10.2f} | 标准差: {stats.get('std', 'N/A'):>10.2f}")
                print(f"    最小值: {stats.get('min', 'N/A'):>8.2f} | 最大值: {stats.get('max', 'N/A'):>10.2f}")
        
        # 文本列信息
        if "文本列信息" in description:
            print("\n📝 文本列信息:")
            text_info = description["文本列信息"]
            for col, info in text_info.items():
                print(f"  {col}: 唯一值 {info['唯一值数量']}, 最常见: '{info['最常见值']}'")
    
    def analyze_all_data(self):
        """分析所有数据文件"""
        print(f"🔍 开始分析数据目录: {self.data_dir}")
        
        data_files = self.get_data_files()
        if not data_files:
            print("❌ 没有找到支持的数据文件")
            return
        
        print(f"📁 找到 {len(data_files)} 个数据文件")
        
        total_datasets = 0
        
        for file_path in data_files:
            print(f"\n🔄 处理文件: {file_path.name}")
            
            if file_path.suffix.lower() == '.csv':
                df = self.read_csv_file(file_path)
                if df is not None:
                    description = self.describe_dataframe(df, file_path.name)
                    self.print_description(description)
                    total_datasets += 1
            
            elif file_path.suffix.lower() == '.parquet':
                df = self.read_parquet_file(file_path)
                if df is not None:
                    description = self.describe_dataframe(df, file_path.name)
                    self.print_description(description)
                    total_datasets += 1
            
            elif file_path.suffix.lower() in ['.duckdb', '.db']:
                tables_data = self.read_duckdb_file(file_path)
                for table_name, df in tables_data.items():
                    description = self.describe_dataframe(df, f"{file_path.name}.{table_name}")
                    self.print_description(description)
                    total_datasets += 1
        
        print(f"\n🎉 分析完成！共处理了 {total_datasets} 个数据集")


def main():
    """主函数"""
    try:
        analyzer = DataAnalyzer()
        analyzer.analyze_all_data()
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")


if __name__ == "__main__":
    main()