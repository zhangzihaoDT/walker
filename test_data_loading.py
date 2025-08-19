#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据加载功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from tasks.analyze_business_metrics import (
    analyze_parquet_file,
    analyze_presale_post_launch_comparison
)

def test_data_loading():
    """测试数据加载"""
    print("=== 测试数据加载 ===")
    
    # 测试业务数据加载
    data_path = "/Users/zihao_/Documents/github/W33_utils_3/data/business_daily_metrics.parquet"
    print(f"测试文件路径: {data_path}")
    print(f"文件存在: {Path(data_path).exists()}")
    
    if Path(data_path).exists():
        print("\n开始加载数据...")
        df = analyze_parquet_file(data_path)
        
        if df is not None:
            print(f"✓ 数据加载成功！")
            print(f"数据形状: {df.shape}")
            print(f"列名: {list(df.columns)[:10]}...")  # 只显示前10列
            
            # 测试Module 4分析
            print("\n测试Module 4分析...")
            try:
                comparison_data = analyze_presale_post_launch_comparison(df)
                if comparison_data:
                    print(f"✓ Module 4分析成功！")
                    print(f"分析结果包含 {len(comparison_data)} 个事件")
                    print(f"事件列表: {list(comparison_data.keys())}")
                else:
                    print("✗ Module 4分析返回空结果")
            except Exception as e:
                print(f"✗ Module 4分析失败: {e}")
        else:
            print("✗ 数据加载失败")
    else:
        print("✗ 数据文件不存在")

if __name__ == "__main__":
    test_data_loading()