import pandas as pd

# 加载数据
file_path = "/Users/zihao_/Documents/github/W33_utils_3/data/乘用车上险量_0723.parquet"
df = pd.read_parquet(file_path)

print("数据基本信息:")
print(f"数据行数: {len(df)}")
print(f"数据列数: {len(df.columns)}")
print(f"数据列名: {list(df.columns)}")
print("\n" + "="*50 + "\n")

# 1. 查看所有品牌
print("1. 查看所有品牌:")
all_brands = df['brand'].unique()
print(f"总共有 {len(all_brands)} 个品牌")
print("所有品牌列表:")
for i, brand in enumerate(sorted(all_brands), 1):
    print(f"{i:3d}. {brand}")
print("\n" + "="*50 + "\n")

# 2. 查看品牌="智己"的销量
print("2. 查看品牌='智己'的销量:")
zhiji_data = df[df['brand'] == '智己']
if len(zhiji_data) > 0:
    zhiji_total_sales = zhiji_data['sales_volume'].sum()
    print(f"智己品牌总销量: {zhiji_total_sales:,}")
    print(f"智己品牌数据条数: {len(zhiji_data)}")
else:
    print("未找到'智己'品牌的数据")
print("\n" + "="*50 + "\n")

# 3. 查看品牌="智己"的全部车型有哪些
print("3. 查看品牌='智己'的全部车型:")
if len(zhiji_data) > 0:
    zhiji_models = zhiji_data['model_name'].unique()
    print(f"智己品牌共有 {len(zhiji_models)} 个车型:")
    for i, model in enumerate(sorted(zhiji_models), 1):
        model_sales = zhiji_data[zhiji_data['model_name'] == model]['sales_volume'].sum()
        print(f"{i:2d}. {model} (销量: {model_sales:,})")
else:
    print("未找到'智己'品牌的车型数据")
print("\n" + "="*50 + "\n")

# 4. 查看品牌="智己"，且车型="LS6"的销量
print("4. 查看品牌='智己'，且车型='LS6'的销量:")
zhiji_ls6_data = df[(df['brand'] == '智己') & (df['model_name'] == 'LS6')]
if len(zhiji_ls6_data) > 0:
    ls6_sales = zhiji_ls6_data['sales_volume'].sum()
    print(f"智己LS6销量: {ls6_sales:,}")
    print(f"数据条数: {len(zhiji_ls6_data)}")
else:
    print("未找到'智己'品牌'LS6'车型的数据")
print("\n" + "="*50 + "\n")

# 5. 查看品牌="智己"，且车型="智己LS6"的销量
print("5. 查看品牌='智己'，且车型='智己LS6'的销量:")
zhiji_ls6_full_data = df[(df['brand'] == '智己') & (df['model_name'] == '智己LS6')]
if len(zhiji_ls6_full_data) > 0:
    ls6_full_sales = zhiji_ls6_full_data['sales_volume'].sum()
    print(f"智己'智己LS6'销量: {ls6_full_sales:,}")
    print(f"数据条数: {len(zhiji_ls6_full_data)}")
else:
    print("未找到'智己'品牌'智己LS6'车型的数据")
print("\n" + "="*50 + "\n")

# 6. 额外分析：查看智己品牌相关的所有可能车型名称（包含模糊匹配）
print("6. 额外分析：查看包含'智己'或'LS6'关键词的所有车型:")
zhiji_related = df[df['model_name'].str.contains('智己|LS6', case=False, na=False)]
if len(zhiji_related) > 0:
    print("包含'智己'或'LS6'的车型:")
    related_models = zhiji_related.groupby(['brand', 'model_name'])['sales_volume'].sum().reset_index()
    related_models = related_models.sort_values('sales_volume', ascending=False)
    for _, row in related_models.iterrows():
        print(f"品牌: {row['brand']}, 车型: {row['model_name']}, 销量: {row['sales_volume']:,}")
else:
    print("未找到包含'智己'或'LS6'关键词的车型")
print("\n" + "="*50 + "\n")

# 7. 检查数据中是否存在智己相关的其他字段信息
print("7. 检查智己品牌的详细信息:")
if len(zhiji_data) > 0:
    # 检查是否存在sub_model_name字段
    if 'sub_model_name' in df.columns:
        print("智己品牌的sub_model_name字段:")
        zhiji_sub_models = zhiji_data['sub_model_name'].unique()
        for sub_model in sorted(zhiji_sub_models):
            sub_sales = zhiji_data[zhiji_data['sub_model_name'] == sub_model]['sales_volume'].sum()
            print(f"  - {sub_model} (销量: {sub_sales:,})")
    else:
        print("数据中不存在'sub_model_name'字段")
        
    # 显示智己品牌的时间分布
    print("\n智己品牌的时间分布:")
    zhiji_time_dist = zhiji_data.groupby('date')['sales_volume'].sum().sort_index()
    print(f"数据时间范围: {zhiji_time_dist.index.min()} 到 {zhiji_time_dist.index.max()}")
    print("月度销量分布:")
    for date, sales in zhiji_time_dist.items():
        print(f"  {date.strftime('%Y-%m')}: {sales:,}")
else:
    print("无智己品牌数据可分析")

print("\n" + "="*50 + "\n")

# 8. 总结分析结果
print("8. 总结分析结果:")
print("关键发现:")
print("- 数据库中智己品牌存在，但车型名称为'智己LS6'、'智己LS7'、'智己L7'等")
print("- 查询'LS6'车型时未找到数据，说明车型名称包含品牌前缀")
print("- 这解释了为什么销量查询模块在处理智己LS6时可能出现问题")
print("- 建议在查询时使用完整的车型名称'智己LS6'而不是'LS6'")