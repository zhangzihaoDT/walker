#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CSV读取功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.run_data_describe import DataAnalyzer

def test_csv_reading():
    """测试CSV文件读取"""
    print("🧪 测试CSV文件读取功能")
    print("=" * 40)
    
    try:
        analyzer = DataAnalyzer()
        csv_files = [
            "订单观察_data.csv",
            "业务数据记录_with表_表格.csv"
        ]
        
        for csv_name in csv_files:
            csv_file = analyzer.data_dir / csv_name
            
            if csv_file.exists():
                print(f"\n📁 测试文件: {csv_file.name}")
                df = analyzer.read_csv_file(csv_file)
                
                if df is not None:
                    print(f"✅ 读取成功!")
                    print(f"📊 数据形状: {df.shape}")
                    print(f"📋 列名: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")
                    print(f"🔍 前3行数据:")
                    print(df.head(3))
                else:
                    print("❌ 读取失败")
            else:
                print(f"❌ 文件不存在: {csv_file}")
                
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_csv_reading()