#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from pathlib import Path

# 加载数据
data_path = Path('data/乘用车上险量_0723.parquet')
if data_path.exists():
    df = pd.read_parquet(data_path)
    print(f"数据加载成功，共 {len(df)} 条记录")
else:
    print("数据文件不存在")
    exit(1)

# 1. 查看所有品牌
print("\n=== 所有品牌 ===")
all_brands = df['brand'].unique()
print(f"品牌总数: {len(all_brands)}")
print("前20个品牌:", sorted(all_brands)[:20])

# 2. 检查特斯拉品牌
print("\n=== 特斯拉品牌检查 ===")
tesla_brands = [brand for brand in all_brands if '特斯拉' in str(brand) or 'tesla' in str(brand).lower()]
print(f"包含'特斯拉'的品牌: {tesla_brands}")

# 3. 查看特斯拉相关车型
print("\n=== 特斯拉相关车型 ===")
tesla_models = df[df['brand'].str.contains('特斯拉', na=False)]['model_name'].unique() if tesla_brands else []
print(f"特斯拉车型: {list(tesla_models)}")

# 4. 检查Model Y相关车型
print("\n=== Model Y相关车型检查 ===")
model_y_variants = df[df['model_name'].str.contains('Model Y', na=False, case=False)]['model_name'].unique()
print(f"包含'Model Y'的车型: {list(model_y_variants)}")

# 5. 检查所有包含'Model'的车型
print("\n=== 所有包含'Model'的车型 ===")
model_variants = df[df['model_name'].str.contains('Model', na=False, case=False)]['model_name'].unique()
print(f"包含'Model'的车型数量: {len(model_variants)}")
print(f"前10个: {list(model_variants)[:10]}")

# 6. 查看特斯拉品牌的销量数据
if tesla_brands:
    print("\n=== 特斯拉品牌销量数据 ===")
    tesla_data = df[df['brand'].isin(tesla_brands)]
    tesla_sales = tesla_data.groupby(['brand', 'model_name'])['sales_volume'].sum().reset_index()
    tesla_sales = tesla_sales.sort_values('sales_volume', ascending=False)
    print(tesla_sales.head(10))
else:
    print("\n❌ 数据库中没有找到特斯拉品牌")

# 7. 检查智己LS6的情况
print("\n=== 智己LS6检查 ===")
zhiji_ls6_exact = df[df['model_name'] == 'LS6']
zhiji_ls6_full = df[df['model_name'] == '智己LS6']
print(f"查询'LS6': {len(zhiji_ls6_exact)} 条记录")
print(f"查询'智己LS6': {len(zhiji_ls6_full)} 条记录")

if len(zhiji_ls6_full) > 0:
    ls6_sales = zhiji_ls6_full['sales_volume'].sum()
    print(f"智己LS6总销量: {ls6_sales:,}")

# 8. 总结分析
print("\n=== 分析总结 ===")
print("关键发现:")
if not tesla_brands:
    print("- 数据库中没有特斯拉品牌数据")
else:
    print(f"- 特斯拉品牌存在: {tesla_brands}")
    print(f"- 特斯拉车型数量: {len(tesla_models)}")

print(f"- 智己LS6查询结果: 使用'LS6'查询到{len(zhiji_ls6_exact)}条，使用'智己LS6'查询到{len(zhiji_ls6_full)}条")
print("- 建议: 检查车型名称的完整性和一致性")