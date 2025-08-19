#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

# 读取线索数据
df = pd.read_parquet('/Users/zihao_/Documents/github/W33_utils_3/data/leads_structure_analysis.parquet')

print('数据形状:', df.shape)
print('\n所有字段:')
for i, col in enumerate(df.columns):
    print(f'{i+1}. {col}')

print('\n数据类型:')
print(df.dtypes)

print('\n前5行数据:')
print(df.head())

# 查找可能的时间字段
time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower() or 'create' in col.lower()]
print('\n可能的时间字段:')
for col in time_cols:
    print(f'- {col}: {df[col].dtype}')
    if not df[col].isna().all():
        print(f'  示例值: {df[col].dropna().head(3).tolist()}')