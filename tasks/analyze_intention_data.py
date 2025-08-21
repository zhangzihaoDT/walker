#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析脚本：读取parquet文件并分析基本信息
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_parquet_data(file_path):
    """
    读取parquet文件并打印基本数据信息
    
    Args:
        file_path (str): parquet文件路径
    """
    try:
        # 读取parquet文件
        print(f"正在读取文件: {file_path}")
        df = pd.read_parquet(file_path)
        
        print("\n" + "="*60)
        print("数据基本信息")
        print("="*60)
        
        # 打印数据形状
        print(f"数据形状: {df.shape} (行数: {df.shape[0]}, 列数: {df.shape[1]})")
        
        print("\n" + "-"*40)
        print("字段信息")
        print("-"*40)
        
        # 打印所有字段名称、类型和空值数量
        print(f"{'字段名':<20} {'数据类型':<15} {'空值数量':<10} {'空值比例':<10}")
        print("-" * 60)
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            null_ratio = f"{(null_count / len(df) * 100):.2f}%"
            print(f"{col:<20} {dtype:<15} {null_count:<10} {null_ratio:<10}")
        
        print("\n" + "-"*40)
        print("数据概览")
        print("-"*40)
        
        # 显示前几行数据
        print("\n前5行数据:")
        print(df.head())
        
        # 数据类型统计
        print("\n数据类型统计:")
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            print(f"{dtype}: {count}个字段")
        
        # 总体统计信息
        print("\n" + "-"*40)
        print("总体统计")
        print("-"*40)
        print(f"总记录数: {len(df):,}")
        print(f"总字段数: {len(df.columns)}")
        print(f"总空值数: {df.isnull().sum().sum():,}")
        print(f"数据完整度: {((df.size - df.isnull().sum().sum()) / df.size * 100):.2f}%")
        
        # 数值型字段的描述性统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            print("\n" + "-"*40)
            print("数值型字段描述性统计")
            print("-"*40)
            print(df[numeric_cols].describe())
        
        # 非数值型字段的唯一值统计
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        if len(categorical_cols) > 0:
            print("\n" + "-"*40)
            print("分类字段唯一值统计")
            print("-"*40)
            for col in categorical_cols:
                unique_count = df[col].nunique()
                print(f"{col}: {unique_count}个唯一值")
                if unique_count <= 10:  # 如果唯一值不多，显示所有值
                    print(f"  值: {list(df[col].unique())}")
        
        return df
        
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None

def calculate_lock_rate_indicator(df):
    """
    计算锁单率指标
    
    Args:
        df (DataFrame): 原始数据
    
    Returns:
        DataFrame: 添加锁单指标的数据
    """
    # 创建锁单指标：Lock_Time不为空表示有锁单记录
    df['has_lock'] = ~df['Lock_Time'].isnull()
    
    print("\n" + "="*60)
    print("锁单率指标分析")
    print("="*60)
    
    total_orders = len(df)
    locked_orders = df['has_lock'].sum()
    lock_rate = (locked_orders / total_orders) * 100
    
    print(f"总订单数: {total_orders:,}")
    print(f"有锁单记录的订单数: {locked_orders:,}")
    print(f"锁单率: {lock_rate:.2f}%")
    
    return df

def analyze_by_vehicle_type(df):
    """
    按车型分析订单结构
    
    Args:
        df (DataFrame): 包含锁单指标的数据
    """
    print("\n" + "="*60)
    print("车型订单结构分析")
    print("="*60)
    
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    # 筛选掉LS7和L7车型
    df_filtered = df[~df['车型分组'].isin(['LS7', 'L7'])]
    
    # 按车型统计订单数和锁单率
    vehicle_analysis = df_filtered.groupby('车型分组', observed=False).agg({
        'Order Number': 'count',
        'has_lock': ['sum', 'mean']
    }).round(4)
    
    vehicle_analysis.columns = ['订单数', '锁单数', '锁单率']
    vehicle_analysis['锁单率'] = vehicle_analysis['锁单率'] * 100
    vehicle_analysis['订单占比'] = (vehicle_analysis['订单数'] / vehicle_analysis['订单数'].sum() * 100).round(2)
    
    # 添加预售天数列
    presale_days = []
    for vehicle in vehicle_analysis.index:
        if vehicle in presale_periods:
            start_date = pd.to_datetime(presale_periods[vehicle]['start'])
            end_date = pd.to_datetime(presale_periods[vehicle]['end'])
            days = (end_date - start_date).days + 1  # 包含起始日期
            presale_days.append(days)
        else:
            presale_days.append(None)
    
    vehicle_analysis['预售天数'] = presale_days
    
    # 确保完全移除LS7和L7车型（如果它们存在于索引中）
    vehicle_analysis = vehicle_analysis[~vehicle_analysis.index.isin(['LS7', 'L7'])]
    
    print("\n车型订单统计:")
    print(vehicle_analysis.sort_values('订单数', ascending=False))
    
    return vehicle_analysis

def analyze_by_demographics(df):
    """
    按人口统计学特征分析
    
    Args:
        df (DataFrame): 包含锁单指标的数据
    """
    print("\n" + "="*60)
    print("人口统计学特征分析")
    print("="*60)
    
    # 处理锁单指标列的数据类型问题
    if 'Has_Intention_Payment' in df.columns:
        if df['Has_Intention_Payment'].dtype.name == 'category':
            # 将分类数据转换为数值，假设 '真' 表示 1，其他表示 0
            df = df.copy()
            df['Has_Intention_Payment'] = df['Has_Intention_Payment'].astype(str).map({
                '真': 1, 'True': 1, 'true': 1, '1': 1,
                '假': 0, 'False': 0, 'false': 0, '0': 0
            }).fillna(0).astype(float)
    
    # 年龄分析
    print("\n1. 年龄分析:")
    # 创建年龄分组
    df['age_group'] = pd.cut(df['buyer_age'], 
                            bins=[0, 25, 35, 45, 55, 100], 
                            labels=['25岁以下', '25-35岁', '35-45岁', '45-55岁', '55岁以上'],
                            include_lowest=True)
    
    age_analysis = df.groupby(['age_group', '车型分组'], observed=False).size().unstack(fill_value=0)
    # 检查锁单指标列是否存在，优先使用 has_lock，如果不存在则使用 Has_Intention_Payment
    lock_column = 'has_lock' if 'has_lock' in df.columns else 'Has_Intention_Payment'
    
    age_summary = df.groupby('age_group', observed=False).agg({
        'Order Number': 'count',
        lock_column: 'mean'
    }).round(4)
    age_summary.columns = ['订单数', '锁单率']
    age_summary['锁单率'] = age_summary['锁单率'] * 100
    # 添加占比列
    age_summary['订单占比(%)'] = (age_summary['订单数'] / age_summary['订单数'].sum() * 100).round(2)
    
    print("年龄组订单统计:")
    print(age_summary)
    print("\n年龄组×车型交叉表:")
    print(age_analysis)
    
    # 年龄组×车型占比分析
    age_vehicle_pct = age_analysis.div(age_analysis.sum().sum()) * 100
    print("\n年龄组×车型占比表(%):")
    print(age_vehicle_pct.round(2))
    
    # 车型平均年龄对比分析（筛选18-70岁数据，排除异常值）
    print("\n3. 车型平均年龄对比分析（18-70岁）:")
    print("-" * 50)
    
    # 筛选18-70岁的数据，排除异常值
    age_filtered_df = df[(df['buyer_age'] >= 18) & (df['buyer_age'] <= 70)]
    
    if len(age_filtered_df) > 0:
        # 计算每个车型的平均年龄
        vehicle_age_stats = age_filtered_df.groupby('车型分组').agg({
            'buyer_age': ['mean', 'median', 'std', 'count']
        }).round(2)
        
        # 重命名列
        vehicle_age_stats.columns = ['平均年龄', '中位数年龄', '年龄标准差', '样本数量']
        
        # 按平均年龄排序
        vehicle_age_stats = vehicle_age_stats.sort_values('平均年龄', ascending=False)
        
        print(f"筛选条件: 18-70岁（原始数据{len(df)}条，筛选后{len(age_filtered_df)}条）")
        print("\n各车型年龄统计:")
        print(vehicle_age_stats)
        
        # 计算整体平均年龄
        overall_mean_age = age_filtered_df['buyer_age'].mean()
        print(f"\n整体平均年龄: {overall_mean_age:.2f}岁")
        
        # 分析各车型与整体平均年龄的差异
        print("\n各车型与整体平均年龄差异:")
        age_diff_analysis = pd.DataFrame({
            '车型': vehicle_age_stats.index,
            '平均年龄': vehicle_age_stats['平均年龄'],
            '与整体差异': (vehicle_age_stats['平均年龄'] - overall_mean_age).round(2),
            '样本数量': vehicle_age_stats['样本数量']
        })
        
        for _, row in age_diff_analysis.iterrows():
            diff = row['与整体差异']
            if diff > 0:
                trend = f"高于整体{diff:.2f}岁"
            elif diff < 0:
                trend = f"低于整体{abs(diff):.2f}岁"
            else:
                trend = "与整体持平"
            print(f"{row['车型']}: {row['平均年龄']:.2f}岁 ({trend}, 样本{row['样本数量']}个)")
        
        # 找出年龄最高和最低的车型
        highest_age_model = vehicle_age_stats.index[0]
        lowest_age_model = vehicle_age_stats.index[-1]
        age_gap = vehicle_age_stats.loc[highest_age_model, '平均年龄'] - vehicle_age_stats.loc[lowest_age_model, '平均年龄']
        
        print(f"\n年龄差异总结:")
        print(f"• 平均年龄最高车型: {highest_age_model} ({vehicle_age_stats.loc[highest_age_model, '平均年龄']:.2f}岁)")
        print(f"• 平均年龄最低车型: {lowest_age_model} ({vehicle_age_stats.loc[lowest_age_model, '平均年龄']:.2f}岁)")
        print(f"• 车型间年龄差距: {age_gap:.2f}岁")
        
    else:
        print("警告: 筛选18-70岁后无有效数据")
    
    # 性别分析
    print("\n4. 性别分析:")
    gender_analysis = df.groupby(['order_gender', '车型分组'], observed=False).size().unstack(fill_value=0)
    gender_summary = df.groupby('order_gender', observed=False).agg({
        'Order Number': 'count',
        lock_column: 'mean'
    }).round(4)
    gender_summary.columns = ['订单数', '锁单率']
    gender_summary['锁单率'] = gender_summary['锁单率'] * 100
    # 添加占比列
    gender_summary['订单占比(%)'] = (gender_summary['订单数'] / gender_summary['订单数'].sum() * 100).round(2)
    
    print("性别订单统计:")
    print(gender_summary)
    print("\n性别×车型交叉表:")
    print(gender_analysis)
    
    # 性别×车型占比分析
    gender_vehicle_pct = gender_analysis.div(gender_analysis.sum().sum()) * 100
    print("\n性别×车型占比表(%):")
    print(gender_vehicle_pct.round(2))
    
    # CM2车型差异解读
    print("\n" + "="*60)
    print("CM2车型人口统计学特征差异解读")
    print("="*60)
    
    # 检查是否有CM2车型数据
    if 'CM2' in df['车型分组'].unique():
        cm2_data = df[df['车型分组'] == 'CM2']
        other_data = df[df['车型分组'] != 'CM2']
        
        print("\n1. CM2车型年龄结构差异:")
        print("-" * 40)
        
        # CM2年龄分布
        cm2_age_dist = cm2_data.groupby('age_group', observed=False).size()
        cm2_age_pct = (cm2_age_dist / cm2_age_dist.sum() * 100).round(2)
        
        # 其他车型年龄分布
        other_age_dist = other_data.groupby('age_group', observed=False).size()
        other_age_pct = (other_age_dist / other_age_dist.sum() * 100).round(2)
        
        # 对比分析
        age_comparison = pd.DataFrame({
            'CM2占比(%)': cm2_age_pct,
            '其他车型占比(%)': other_age_pct
        }).fillna(0)
        age_comparison['差异(百分点)'] = (age_comparison['CM2占比(%)'] - age_comparison['其他车型占比(%)']).round(2)
        
        print(age_comparison)
        
        # 年龄差异解读
        max_diff_age = age_comparison['差异(百分点)'].abs().idxmax()
        max_diff_value = age_comparison.loc[max_diff_age, '差异(百分点)']
        
        if max_diff_value > 0:
            print(f"\n年龄特征解读: CM2车型在{max_diff_age}群体中占比显著高于其他车型({max_diff_value:+.2f}个百分点)")
        else:
            print(f"\n年龄特征解读: CM2车型在{max_diff_age}群体中占比显著低于其他车型({max_diff_value:+.2f}个百分点)")
        
        print("\n2. CM2车型性别结构差异:")
        print("-" * 40)
        
        # CM2性别分布
        cm2_gender_dist = cm2_data.groupby('order_gender', observed=False).size()
        cm2_gender_pct = (cm2_gender_dist / cm2_gender_dist.sum() * 100).round(2)
        
        # 其他车型性别分布
        other_gender_dist = other_data.groupby('order_gender', observed=False).size()
        other_gender_pct = (other_gender_dist / other_gender_dist.sum() * 100).round(2)
        
        # 对比分析
        gender_comparison = pd.DataFrame({
            'CM2占比(%)': cm2_gender_pct,
            '其他车型占比(%)': other_gender_pct
        }).fillna(0)
        gender_comparison['差异(百分点)'] = (gender_comparison['CM2占比(%)'] - gender_comparison['其他车型占比(%)']).round(2)
        
        print(gender_comparison)
        
        # 性别差异解读
        max_diff_gender = gender_comparison['差异(百分点)'].abs().idxmax()
        max_diff_value_gender = gender_comparison.loc[max_diff_gender, '差异(百分点)']
        
        if max_diff_value_gender > 0:
            print(f"\n性别特征解读: CM2车型在{max_diff_gender}群体中占比显著高于其他车型({max_diff_value_gender:+.2f}个百分点)")
        else:
            print(f"\n性别特征解读: CM2车型在{max_diff_gender}群体中占比显著低于其他车型({max_diff_value_gender:+.2f}个百分点)")
        
        # 综合特征分析
        print("\n3. CM2车型综合特征分析:")
        print("-" * 40)
        
        cm2_total = len(cm2_data)
        other_total = len(other_data)
        total_orders = len(df)
        
        print(f"CM2车型订单数: {cm2_total:,} ({cm2_total/total_orders*100:.2f}%)")
        print(f"其他车型订单数: {other_total:,} ({other_total/total_orders*100:.2f}%)")
        
        # 锁单率对比
        cm2_lock_rate = cm2_data[lock_column].mean() * 100
        other_lock_rate = other_data[lock_column].mean() * 100
        
        print(f"\nCM2车型锁单率: {cm2_lock_rate:.2f}%")
        print(f"其他车型锁单率: {other_lock_rate:.2f}%")
        print(f"锁单率差异: {cm2_lock_rate - other_lock_rate:+.2f}个百分点")
        
    else:
        print("\n注意: 数据中未发现CM2车型，无法进行差异对比分析。")

def analyze_by_geography(df):
    """
    按地理位置分析不同车型的分布特征
    
    Args:
        df (DataFrame): 包含锁单指标的数据
    """
    print("\n" + "="*60)
    print("车型地理分布分析")
    print("="*60)
    
    def calculate_concentration_index(series):
        """计算集中度指数(基尼系数)"""
        if len(series) <= 1:
            return 0
        sorted_values = np.sort(series)
        n = len(series)
        cumsum = np.cumsum(sorted_values)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
    
    # 1. 城市等级分析
    print("\n1. 城市等级分布分析")
    print("=" * 40)
    
    city_level_vehicle = df.groupby(['license_city_level', '车型分组'], observed=False).size().unstack(fill_value=0)
    city_level_total = city_level_vehicle.sum(axis=1)
    city_level_pct = city_level_vehicle.div(city_level_vehicle.sum().sum()) * 100
    
    print("\n各车型在不同城市等级的订单数量:")
    print(city_level_vehicle)
    
    print("\n各车型在不同城市等级的占比(%):")
    print(city_level_pct.round(2))
    
    # 计算各车型在不同城市等级的锁单率
    print("\n各车型在不同城市等级的锁单率(%):")
    city_level_lock_rates = {}
    for vehicle in city_level_vehicle.columns:
        vehicle_lock_rates = []
        for city_level in city_level_vehicle.index:
            city_level_data = df[(df['车型分组'] == vehicle) & (df['license_city_level'] == city_level)]
            lock_rate = city_level_data['has_lock'].mean() * 100 if len(city_level_data) > 0 else 0
            vehicle_lock_rates.append(round(lock_rate, 2))
        city_level_lock_rates[vehicle] = vehicle_lock_rates
    
    city_level_lock_df = pd.DataFrame(city_level_lock_rates, index=city_level_vehicle.index)
    print(city_level_lock_df)
    
    # 计算各车型的城市等级集中度
    print("\n各车型城市等级集中度分析:")
    concentration_city_level = {}
    for vehicle in city_level_vehicle.columns:
        if city_level_vehicle[vehicle].sum() > 0:
            concentration = calculate_concentration_index(city_level_vehicle[vehicle].values)
            concentration_city_level[vehicle] = concentration
    
    concentration_df_city = pd.DataFrame(list(concentration_city_level.items()), 
                                        columns=['车型', '城市等级集中度']).sort_values('城市等级集中度', ascending=False)
    print(concentration_df_city.round(4))
    
    # 2. 省份分析
    print("\n2. 省份分布分析")
    print("=" * 40)
    
    province_vehicle = df.groupby(['License Province', '车型分组'], observed=False).size().unstack(fill_value=0)
    province_pct = province_vehicle.div(province_vehicle.sum().sum()) * 100
    
    # 显示各车型TOP10省份
    for vehicle in province_vehicle.columns:
        if province_vehicle[vehicle].sum() > 0:
            top_provinces = province_vehicle[vehicle].sort_values(ascending=False).head(10)
            top_provinces_pct = (top_provinces / province_vehicle[vehicle].sum() * 100).round(2)
            
            # 计算各省份的锁单率
            lock_rates = []
            for province in top_provinces.index:
                province_data = df[(df['车型分组'] == vehicle) & (df['License Province'] == province)]
                lock_rate = province_data['has_lock'].mean() * 100 if len(province_data) > 0 else 0
                lock_rates.append(round(lock_rate, 2))
            
            print(f"\n{vehicle}车型TOP10省份分布:")
            result_df = pd.DataFrame({
                '订单数': top_provinces,
                '占该车型比例(%)': top_provinces_pct,
                '锁单率(%)': lock_rates
            })
            print(result_df)
    
    # 计算各车型的省份集中度
    print("\n各车型省份集中度分析:")
    concentration_province = {}
    for vehicle in province_vehicle.columns:
        if province_vehicle[vehicle].sum() > 0:
            concentration = calculate_concentration_index(province_vehicle[vehicle].values)
            concentration_province[vehicle] = concentration
    
    concentration_df_province = pd.DataFrame(list(concentration_province.items()), 
                                           columns=['车型', '省份集中度']).sort_values('省份集中度', ascending=False)
    print(concentration_df_province.round(4))
    
    # 3. 城市分析（基于License City）
    print("\n3. 城市分布分析")
    print("=" * 40)
    
    # 检查是否有License City字段
    if 'License City' in df.columns:
        city_vehicle = df.groupby(['License City', '车型分组'], observed=False).size().unstack(fill_value=0)
        
        # 显示各车型TOP10城市
        for vehicle in city_vehicle.columns:
            if city_vehicle[vehicle].sum() > 0:
                top_cities = city_vehicle[vehicle].sort_values(ascending=False).head(10)
                top_cities_pct = (top_cities / city_vehicle[vehicle].sum() * 100).round(2)
                
                # 计算各城市的锁单率
                lock_rates = []
                for city in top_cities.index:
                    city_data = df[(df['车型分组'] == vehicle) & (df['License City'] == city)]
                    lock_rate = city_data['has_lock'].mean() * 100 if len(city_data) > 0 else 0
                    lock_rates.append(round(lock_rate, 2))
                
                print(f"\n{vehicle}车型TOP10城市分布:")
                result_df = pd.DataFrame({
                    '订单数': top_cities,
                    '占该车型比例(%)': top_cities_pct,
                    '锁单率(%)': lock_rates
                })
                print(result_df)
        
        # 计算各车型的城市集中度
        print("\n各车型城市集中度分析:")
        concentration_city = {}
        for vehicle in city_vehicle.columns:
            if city_vehicle[vehicle].sum() > 0:
                concentration = calculate_concentration_index(city_vehicle[vehicle].values)
                concentration_city[vehicle] = concentration
        
        concentration_df_city_detail = pd.DataFrame(list(concentration_city.items()), 
                                                   columns=['车型', '城市集中度']).sort_values('城市集中度', ascending=False)
        print(concentration_df_city_detail.round(4))
    else:
        print("\n注意: 数据中未发现License City字段，跳过城市分析。")
    
    # 4. CM2车型差异解读
    print("\n" + "="*60)
    print("CM2车型地理分布差异解读")
    print("="*60)
    
    target_vehicles = ['CM0', 'CM1', 'DM1']
    available_vehicles = [v for v in target_vehicles if v in df['车型分组'].unique()]
    
    if 'CM2' in df['车型分组'].unique() and len(available_vehicles) > 0:
        
        # 城市等级差异分析
        print("\n1. 城市等级分布差异分析")
        print("-" * 50)
        
        cm2_city_level = df[df['车型分组'] == 'CM2'].groupby('license_city_level', observed=False).size()
        cm2_city_level_pct = (cm2_city_level / cm2_city_level.sum() * 100).round(2)
        
        comparison_results = []
        for vehicle in available_vehicles:
            other_city_level = df[df['车型分组'] == vehicle].groupby('license_city_level', observed=False).size()
            other_city_level_pct = (other_city_level / other_city_level.sum() * 100).round(2)
            
            # 计算差异
            comparison = pd.DataFrame({
                f'CM2占比(%)': cm2_city_level_pct,
                f'{vehicle}占比(%)': other_city_level_pct
            }).fillna(0)
            comparison['差异(百分点)'] = (comparison[f'CM2占比(%)'] - comparison[f'{vehicle}占比(%)']).round(2)
            
            print(f"\nCM2 vs {vehicle} 城市等级分布对比:")
            print(comparison)
            
            # 找出最大差异
            max_diff_idx = comparison['差异(百分点)'].abs().idxmax()
            max_diff_value = comparison.loc[max_diff_idx, '差异(百分点)']
            
            if max_diff_value > 0:
                print(f"解读: CM2在{max_diff_idx}城市的占比比{vehicle}高{max_diff_value:.2f}个百分点")
            else:
                print(f"解读: CM2在{max_diff_idx}城市的占比比{vehicle}低{abs(max_diff_value):.2f}个百分点")
        
        # 集中度对比分析
        print("\n2. 地理集中度对比分析")
        print("-" * 50)
        
        # 城市等级集中度对比
        print("\n城市等级集中度对比:")
        cm2_concentration_city_level = concentration_city_level.get('CM2', 0)
        print(f"CM2城市等级集中度: {cm2_concentration_city_level:.4f}")
        
        for vehicle in available_vehicles:
            other_concentration = concentration_city_level.get(vehicle, 0)
            diff = cm2_concentration_city_level - other_concentration
            print(f"{vehicle}城市等级集中度: {other_concentration:.4f} (差异: {diff:+.4f})")
        
        # 省份集中度对比
        print("\n省份集中度对比:")
        cm2_concentration_province = concentration_province.get('CM2', 0)
        print(f"CM2省份集中度: {cm2_concentration_province:.4f}")
        
        for vehicle in available_vehicles:
            other_concentration = concentration_province.get(vehicle, 0)
            diff = cm2_concentration_province - other_concentration
            print(f"{vehicle}省份集中度: {other_concentration:.4f} (差异: {diff:+.4f})")
        
        # 综合解读
        print("\n3. 综合地理特征解读")
        print("-" * 50)
        
        # 计算CM2的地理分布特征
        cm2_data = df[df['车型分组'] == 'CM2']
        cm2_total = len(cm2_data)
        
        # 城市等级分布特征
        cm2_city_level_dist = cm2_data.groupby('license_city_level', observed=False).size().sort_values(ascending=False)
        top_city_level = cm2_city_level_dist.index[0]
        top_city_level_pct = (cm2_city_level_dist.iloc[0] / cm2_total * 100)
        
        print(f"CM2车型主要集中在{top_city_level}城市，占比{top_city_level_pct:.2f}%")
        
        # 省份分布特征
        cm2_province_dist = cm2_data.groupby('License Province', observed=False).size().sort_values(ascending=False)
        top3_provinces = cm2_province_dist.head(3)
        top3_pct = (top3_provinces.sum() / cm2_total * 100)
        
        print(f"CM2车型前3省份({', '.join(top3_provinces.index)})占比{top3_pct:.2f}%")
        
        # 与其他车型的差异总结
        avg_other_concentration_province = np.mean([concentration_province.get(v, 0) for v in available_vehicles])
        if cm2_concentration_province > avg_other_concentration_province:
            print(f"CM2车型地理分布相对更集中，省份集中度比其他车型平均高{cm2_concentration_province - avg_other_concentration_province:.4f}")
        else:
            print(f"CM2车型地理分布相对更分散，省份集中度比其他车型平均低{avg_other_concentration_province - cm2_concentration_province:.4f}")
        
    else:
        missing_vehicles = [v for v in ['CM2'] + target_vehicles if v not in df['车型分组'].unique()]
        print(f"\n注意: 数据中缺少以下车型，无法进行完整的差异对比分析: {', '.join(missing_vehicles)}")

def analyze_by_channel(df):
    """
    分析模块6：渠道结构分析 - 基于first_middle_channel_name的车型分布分析
    
    Args:
        df (DataFrame): 包含锁单指标的数据
    """
    print("\n" + "="*60)
    print("分析模块6：渠道结构分析 - 车型在first_middle_channel_name的分布")
    print("="*60)
    
    # 检查必要字段
    if 'first_middle_channel_name' not in df.columns:
        print("警告：数据中缺少 'first_middle_channel_name' 字段")
        return {}
    
    if '车型分组' not in df.columns:
        print("警告：数据中缺少 '车型分组' 字段")
        return {}
    
    # 按车型和first_middle_channel_name分组分析
    channel_vehicle_analysis = df.groupby(['车型分组', 'first_middle_channel_name'], observed=False).agg({
        'Order Number': 'count'
    }).reset_index()
    channel_vehicle_analysis.rename(columns={'Order Number': 'quantity'}, inplace=True)
    
    # 计算每个车型的总订单数
    vehicle_totals = df.groupby('车型分组', observed=False)['Order Number'].count().to_dict()
    
    # 计算每个渠道的总订单数
    channel_totals = df.groupby('first_middle_channel_name', observed=False)['Order Number'].count().to_dict()
    total_orders = len(df)
    
    # 为每个车型计算占比
    channel_vehicle_analysis['proportion'] = channel_vehicle_analysis.apply(
        lambda row: (row['quantity'] / vehicle_totals[row['车型分组']] * 100) if vehicle_totals[row['车型分组']] > 0 else 0, 
        axis=1
    )
    
    # 计算集中度（使用基尼系数的简化版本）
    def calculate_concentration(vehicle_data):
        if len(vehicle_data) <= 1:
            return 100.0
        
        quantities = vehicle_data['quantity'].values
        quantities = np.sort(quantities)
        n = len(quantities)
        cumsum = np.cumsum(quantities)
        
        # 基尼系数计算
        gini = (2 * np.sum((np.arange(1, n+1) * quantities))) / (n * np.sum(quantities)) - (n + 1) / n
        concentration = gini * 100
        return round(concentration, 2)
    
    print("\n各车型在first_middle_channel_name的分布分析:")
    print("=" * 80)
    
    vehicle_types = sorted(df['车型分组'].unique())
    
    for vehicle in vehicle_types:
        vehicle_data = channel_vehicle_analysis[channel_vehicle_analysis['车型分组'] == vehicle].copy()
        vehicle_data = vehicle_data.sort_values('quantity', ascending=False)
        
        concentration = calculate_concentration(vehicle_data)
        
        print(f"\n{vehicle}车型渠道分布 (集中度: {concentration}):")
        print("-" * 70)
        print(f"{'渠道名称':<25} {'数量':<8} {'占比':<10} {'锁单率':<10} {'渠道占有率':<12}")
        print("-" * 70)
        
        for _, row in vehicle_data.iterrows():
            # 计算该车型在该渠道的锁单率
            vehicle_channel_data = df[(df['车型分组'] == vehicle) & (df['first_middle_channel_name'] == row['first_middle_channel_name'])]
            lock_rate = vehicle_channel_data['has_lock'].mean() * 100 if len(vehicle_channel_data) > 0 else 0
            channel_share = (row['quantity'] / channel_totals[row['first_middle_channel_name']] * 100) if channel_totals[row['first_middle_channel_name']] > 0 else 0
            print(f"{row['first_middle_channel_name']:<25} {row['quantity']:<8} {row['proportion']:<10.2f}% {lock_rate:<10.2f}% {channel_share:<12.2f}%")
    
    # CM2车型差异解读
    print("\n\n" + "="*80)
    print("CM2车型相对CM0、CM1、DM1车型的渠道分布差异解读")
    print("="*80)
    
    cm2_data = channel_vehicle_analysis[channel_vehicle_analysis['车型分组'] == 'CM2']
    cm0_data = channel_vehicle_analysis[channel_vehicle_analysis['车型分组'] == 'CM0']
    cm1_data = channel_vehicle_analysis[channel_vehicle_analysis['车型分组'] == 'CM1']
    dm1_data = channel_vehicle_analysis[channel_vehicle_analysis['车型分组'] == 'DM1']
    
    if len(cm2_data) > 0:
        cm2_concentration = calculate_concentration(cm2_data)
        
        print(f"\nCM2车型渠道分布特征:")
        print("-" * 50)
        print(f"• 渠道集中度: {cm2_concentration}")
        print(f"• 主要渠道分布:")
        
        cm2_top_channels = cm2_data.sort_values('quantity', ascending=False).head(5)
        for _, row in cm2_top_channels.iterrows():
            print(f"  - {row['first_middle_channel_name']}: {row['quantity']}单 ({row['proportion']:.1f}%)")
        
        # 与其他车型对比
        comparisons = []
        if len(cm0_data) > 0:
            cm0_concentration = calculate_concentration(cm0_data)
            comparisons.append(('CM0', cm0_concentration, cm0_data))
        if len(cm1_data) > 0:
            cm1_concentration = calculate_concentration(cm1_data)
            comparisons.append(('CM1', cm1_concentration, cm1_data))
        if len(dm1_data) > 0:
            dm1_concentration = calculate_concentration(dm1_data)
            comparisons.append(('DM1', dm1_concentration, dm1_data))
        
        if comparisons:
            print(f"\n与其他车型对比分析:")
            print("-" * 50)
            
            for model, concentration, model_data in comparisons:
                conc_diff = cm2_concentration - concentration
                conc_trend = "更集中" if conc_diff > 5 else "更分散" if conc_diff < -5 else "相近"
                
                print(f"\n相对{model}车型:")
                print(f"• 集中度差异: {conc_diff:+.1f} ({conc_trend})")
                
                # 分析共同渠道的订单数量和占比差异
                cm2_channels = set(cm2_data['first_middle_channel_name'])
                model_channels = set(model_data['first_middle_channel_name'])
                common_channels = cm2_channels & model_channels
                
                if common_channels:
                    print(f"• 共同渠道数: {len(common_channels)}")
                    
                    # 详细对比每个渠道的订单数量和占比
                    channel_comparisons = []
                    for channel in common_channels:
                        cm2_channel = cm2_data[cm2_data['first_middle_channel_name'] == channel].iloc[0]
                        model_channel = model_data[model_data['first_middle_channel_name'] == channel].iloc[0]
                        
                        cm2_quantity = cm2_channel['quantity']
                        cm2_prop = cm2_channel['proportion']
                        model_quantity = model_channel['quantity']
                        model_prop = model_channel['proportion']
                        
                        quantity_diff = cm2_quantity - model_quantity
                        prop_diff = cm2_prop - model_prop
                        
                        channel_comparisons.append({
                            'channel': channel,
                            'cm2_quantity': cm2_quantity,
                            'model_quantity': model_quantity,
                            'quantity_diff': quantity_diff,
                            'cm2_prop': cm2_prop,
                            'model_prop': model_prop,
                            'prop_diff': prop_diff
                        })
                    
                    # 按占比差异排序，显示最显著的差异
                    channel_comparisons.sort(key=lambda x: abs(x['prop_diff']), reverse=True)
                    
                    print(f"• 主要渠道差异对比:")
                    print(f"  {'渠道':<15} {'CM2订单':<8} {'CM2占比':<8} {model+'订单':<8} {model+'占比':<8} {'占比差异':<8}")
                    print(f"  {'-'*70}")
                    
                    for comp in channel_comparisons[:8]:  # 显示前8个渠道
                        print(f"  {comp['channel']:<15} {comp['cm2_quantity']:<8} {comp['cm2_prop']:<7.1f}% {comp['model_quantity']:<8} {comp['model_prop']:<7.1f}% {comp['prop_diff']:+6.1f}%")
                    
                    # 突出显示显著差异的渠道
                    significant_diffs = [comp for comp in channel_comparisons if abs(comp['prop_diff']) > 5]
                    if significant_diffs:
                        print(f"\n• 显著差异渠道(占比差异>5%):")
                        for comp in significant_diffs[:5]:
                            trend = "更依赖" if comp['prop_diff'] > 0 else "较少依赖"
                            print(f"  - {comp['channel']}: {trend} ({comp['prop_diff']:+.1f}%, CM2: {comp['cm2_quantity']}单 vs {model}: {comp['model_quantity']}单)")
                
                # 找出CM2独有的渠道
                cm2_unique = cm2_channels - model_channels
                if cm2_unique:
                    cm2_unique_data = cm2_data[cm2_data['first_middle_channel_name'].isin(cm2_unique)]
                    cm2_unique_sorted = cm2_unique_data.sort_values('quantity', ascending=False)
                    print(f"• CM2独有渠道({len(cm2_unique)}个):")
                    for _, row in cm2_unique_sorted.head(3).iterrows():
                        print(f"  - {row['first_middle_channel_name']}: {row['quantity']}单 ({row['proportion']:.1f}%)")
                
                # 找出其他车型独有的渠道
                model_unique = model_channels - cm2_channels
                if model_unique:
                    model_unique_data = model_data[model_data['first_middle_channel_name'].isin(model_unique)]
                    model_unique_sorted = model_unique_data.sort_values('quantity', ascending=False)
                    print(f"• {model}独有渠道({len(model_unique)}个):")
                    for _, row in model_unique_sorted.head(3).iterrows():
                        print(f"  - {row['first_middle_channel_name']}: {row['quantity']}单 ({row['proportion']:.1f}%)")
        
        # 渠道策略建议
        print(f"\n渠道策略解读:")
        print("-" * 50)
        
        if cm2_concentration > 70:
            print("• CM2车型渠道高度集中，建议关注主要渠道的稳定性和拓展潜力")
        elif cm2_concentration < 30:
            print("• CM2车型渠道分布较为分散，具有多元化渠道优势")
        else:
            print("• CM2车型渠道分布适中，平衡了集中度和多样性")
        
        # 分析渠道效率
        cm2_avg_per_channel = cm2_data['quantity'].mean()
        print(f"• 平均每渠道订单量: {cm2_avg_per_channel:.1f}单")
        
        if len(comparisons) > 0:
            other_avg = np.mean([data['quantity'].mean() for _, _, data in comparisons])
            efficiency_diff = (cm2_avg_per_channel - other_avg) / other_avg * 100
            efficiency_trend = "更高" if efficiency_diff > 10 else "更低" if efficiency_diff < -10 else "相近"
            print(f"• 相对其他车型渠道效率: {efficiency_trend} ({efficiency_diff:+.1f}%)")
    
    else:
        print("\n未找到CM2车型数据，无法进行差异分析")
    
    return {
        'channel_vehicle_analysis': channel_vehicle_analysis,
        'vehicle_totals': vehicle_totals,
        'channel_totals': channel_totals
    }

def analyze_order_date_features(df):
    """
    分析模块7：下订日期特征分析
    
    Args:
        df (DataFrame): 包含订单数据的DataFrame
    """
    print("\n" + "="*60)
    print("分析模块7：下订日期特征分析")
    print("="*60)
    
    # 定义各车型预售时间范围
    presale_periods = {
        'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
        'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
        'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
        'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
        'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
    }
    
    # 确保时间字段为datetime类型
    df['Intention_Payment_Time'] = pd.to_datetime(df['Intention_Payment_Time'])
    
    # 筛选出CM0、CM1、DM0、DM1车型
    target_vehicles = ['CM0', 'CM1', 'DM0', 'DM1']
    df_filtered = df[df['车型分组'].isin(target_vehicles)].copy()
    
    print("\n各车型预售期间下订日期分布分析:")
    print("="*60)
    
    date_analysis_results = {}
    
    for vehicle in target_vehicles:
        if vehicle not in presale_periods:
            continue
            
        vehicle_data = df_filtered[df_filtered['车型分组'] == vehicle].copy()
        
        if len(vehicle_data) == 0:
            print(f"\n{vehicle}车型: 无订单数据")
            continue
            
        # 获取预售时间范围
        presale_start = pd.to_datetime(presale_periods[vehicle]['start'])
        presale_end = pd.to_datetime(presale_periods[vehicle]['end'])
        total_days = (presale_end - presale_start).days + 1
        
        # 筛选预售期间的订单
        presale_orders = vehicle_data[
            (vehicle_data['Intention_Payment_Time'] >= presale_start) & 
            (vehicle_data['Intention_Payment_Time'] <= presale_end)
        ].copy()
        
        if len(presale_orders) == 0:
            print(f"\n{vehicle}车型: 预售期间无订单数据")
            continue
            
        # 计算每天相对于预售开始的天数
        presale_orders['days_from_start'] = (presale_orders['Intention_Payment_Time'] - presale_start).dt.days
        presale_orders['date_percentage'] = (presale_orders['days_from_start'] / (total_days - 1)) * 100
        
        # 按日期分组统计
        daily_stats = presale_orders.groupby('Intention_Payment_Time', observed=False).agg({
            'Order Number': 'count',
            'has_lock': ['sum', 'mean']
        }).round(4)
        
        daily_stats.columns = ['订单数', '锁单数', '锁单率']
        daily_stats['锁单率'] = daily_stats['锁单率'] * 100
        daily_stats = daily_stats.reset_index()
        daily_stats['相对天数'] = (daily_stats['Intention_Payment_Time'] - presale_start).dt.days
        daily_stats['进度百分比'] = (daily_stats['相对天数'] / (total_days - 1)) * 100
        
        # 计算前10%和后10%的数据
        front_10_threshold = total_days * 0.1
        back_10_threshold = total_days * 0.9
        
        front_10_orders = presale_orders[presale_orders['days_from_start'] <= front_10_threshold]
        back_10_orders = presale_orders[presale_orders['days_from_start'] >= back_10_threshold]
        
        # 统计前10%和后10%的指标
        front_10_count = len(front_10_orders)
        front_10_lock_rate = front_10_orders['has_lock'].mean() * 100 if len(front_10_orders) > 0 else 0
        
        back_10_count = len(back_10_orders)
        back_10_lock_rate = back_10_orders['has_lock'].mean() * 100 if len(back_10_orders) > 0 else 0
        
        # 计算中间80%的数据作为对比
        middle_80_orders = presale_orders[
            (presale_orders['days_from_start'] > front_10_threshold) & 
            (presale_orders['days_from_start'] < back_10_threshold)
        ]
        middle_80_count = len(middle_80_orders)
        middle_80_lock_rate = middle_80_orders['has_lock'].mean() * 100 if len(middle_80_orders) > 0 else 0
        
        print(f"\n{vehicle}车型预售期分析 ({presale_start.strftime('%Y-%m-%d')} 至 {presale_end.strftime('%Y-%m-%d')}, 共{total_days}天):")
        print("-" * 70)
        print(f"{'时间段':<15} {'订单数':<10} {'锁单率(%)':<12} {'占总订单比(%)':<15}")
        print("-" * 70)
        
        total_presale_orders = len(presale_orders)
        
        print(f"{'前10%时间':<15} {front_10_count:<10} {front_10_lock_rate:<12.2f} {(front_10_count/total_presale_orders*100):<15.2f}")
        print(f"{'中间80%时间':<15} {middle_80_count:<10} {middle_80_lock_rate:<12.2f} {(middle_80_count/total_presale_orders*100):<15.2f}")
        print(f"{'后10%时间':<15} {back_10_count:<10} {back_10_lock_rate:<12.2f} {(back_10_count/total_presale_orders*100):<15.2f}")
        
        # 保存分析结果
        date_analysis_results[vehicle] = {
            'total_days': total_days,
            'total_orders': total_presale_orders,
            'front_10_orders': front_10_count,
            'front_10_lock_rate': front_10_lock_rate,
            'middle_80_orders': middle_80_count,
            'middle_80_lock_rate': middle_80_lock_rate,
            'back_10_orders': back_10_count,
            'back_10_lock_rate': back_10_lock_rate,
            'daily_stats': daily_stats
        }
        
        # 显示每日订单趋势（前5天和后5天）
        print(f"\n{vehicle}车型每日订单详情:")
        print("-" * 80)
        print(f"{'日期':<12} {'相对天数':<8} {'进度%':<8} {'订单数':<8} {'锁单数':<8} {'锁单率(%)':<10}")
        print("-" * 80)
        
        # 显示前5天
        front_days = daily_stats.head(5)
        for _, row in front_days.iterrows():
            print(f"{row['Intention_Payment_Time'].strftime('%Y-%m-%d'):<12} {row['相对天数']:<8} {row['进度百分比']:<8.1f} {row['订单数']:<8} {row['锁单数']:<8} {row['锁单率']:<10.2f}")
        
        if len(daily_stats) > 10:
            print("    ...")
            # 显示后5天
            back_days = daily_stats.tail(5)
            for _, row in back_days.iterrows():
                print(f"{row['Intention_Payment_Time'].strftime('%Y-%m-%d'):<12} {row['相对天数']:<8} {row['进度百分比']:<8.1f} {row['订单数']:<8} {row['锁单数']:<8} {row['锁单率']:<10.2f}")
    
    # 跨车型对比分析
    print("\n\n" + "="*80)
    print("跨车型下订日期特征对比分析")
    print("="*80)
    
    if len(date_analysis_results) > 1:
        print("\n各车型预售期订单分布对比:")
        print("-" * 90)
        print(f"{'车型':<8} {'预售天数':<10} {'总订单':<10} {'前10%订单':<12} {'前10%锁单率':<15} {'后10%订单':<12} {'后10%锁单率':<15}")
        print("-" * 90)
        
        for vehicle, data in date_analysis_results.items():
            print(f"{vehicle:<8} {data['total_days']:<10} {data['total_orders']:<10} {data['front_10_orders']:<12} {data['front_10_lock_rate']:<15.2f} {data['back_10_orders']:<12} {data['back_10_lock_rate']:<15.2f}")
        
        # 分析规律
        print("\n下订日期特征规律分析:")
        print("-" * 50)
        
        # 计算前10%和后10%的平均表现
        front_order_ratios = []
        back_order_ratios = []
        front_lock_rates = []
        back_lock_rates = []
        
        for vehicle, data in date_analysis_results.items():
            front_ratio = (data['front_10_orders'] / data['total_orders']) * 100
            back_ratio = (data['back_10_orders'] / data['total_orders']) * 100
            
            front_order_ratios.append(front_ratio)
            back_order_ratios.append(back_ratio)
            front_lock_rates.append(data['front_10_lock_rate'])
            back_lock_rates.append(data['back_10_lock_rate'])
        
        avg_front_ratio = np.mean(front_order_ratios)
        avg_back_ratio = np.mean(back_order_ratios)
        avg_front_lock = np.mean(front_lock_rates)
        avg_back_lock = np.mean(back_lock_rates)
        
        print(f"• 前10%时间段平均订单占比: {avg_front_ratio:.2f}%")
        print(f"• 后10%时间段平均订单占比: {avg_back_ratio:.2f}%")
        print(f"• 前10%时间段平均锁单率: {avg_front_lock:.2f}%")
        print(f"• 后10%时间段平均锁单率: {avg_back_lock:.2f}%")
        
        # 发现规律
        if avg_front_ratio > avg_back_ratio:
            print(f"• 规律发现: 预售前期订单集中度更高 (前期{avg_front_ratio:.1f}% vs 后期{avg_back_ratio:.1f}%)")
        else:
            print(f"• 规律发现: 预售后期订单集中度更高 (后期{avg_back_ratio:.1f}% vs 前期{avg_front_ratio:.1f}%)")
            
        if avg_front_lock > avg_back_lock:
            print(f"• 规律发现: 预售前期锁单率更高 (前期{avg_front_lock:.1f}% vs 后期{avg_back_lock:.1f}%)")
        else:
            print(f"• 规律发现: 预售后期锁单率更高 (后期{avg_back_lock:.1f}% vs 前期{avg_front_lock:.1f}%)")
        
        # CM2预测建议
        print("\n\nCM2车型预售策略建议:")
        print("-" * 50)
        
        cm2_presale_days = (pd.to_datetime(presale_periods['CM2']['end']) - pd.to_datetime(presale_periods['CM2']['start'])).days + 1
        
        print(f"• CM2预售周期: {cm2_presale_days}天 ({presale_periods['CM2']['start']} 至 {presale_periods['CM2']['end']})")
        
        if avg_front_ratio > 15:
            print(f"• 基于历史规律，预计CM2前{int(cm2_presale_days*0.1)}天将获得约{avg_front_ratio:.1f}%的订单")
            print(f"• 建议在预售前期加强营销推广和渠道准备")
        
        if avg_back_ratio > 15:
            print(f"• 基于历史规律，预计CM2后{int(cm2_presale_days*0.1)}天将获得约{avg_back_ratio:.1f}%的订单")
            print(f"• 建议在预售后期加强促销活动和紧迫感营造")
        
        if abs(avg_front_lock - avg_back_lock) > 5:
            better_period = "前期" if avg_front_lock > avg_back_lock else "后期"
            better_rate = max(avg_front_lock, avg_back_lock)
            print(f"• 基于历史规律，预售{better_period}锁单率更高({better_rate:.1f}%)，建议重点关注该时期的转化优化")
        
        # 深度规律性分析
        print("\n\n" + "="*80)
        print("跨车型预售日期特征规律性深度解读")
        print("="*80)
        
        # 分析订单分布一致性
        front_ratios = [data['front_10_ratio'] for data in date_analysis_results.values() if 'front_10_ratio' in data]
        middle_ratios = [data['middle_80_ratio'] for data in date_analysis_results.values() if 'middle_80_ratio' in data]
        back_ratios = [data['back_10_ratio'] for data in date_analysis_results.values() if 'back_10_ratio' in data]
        
        # 如果没有找到这些键，使用已计算的值
        if not front_ratios:
            front_ratios = front_order_ratios
        if not middle_ratios:
            middle_ratios = [100 - f - b for f, b in zip(front_order_ratios, back_order_ratios)]
        if not back_ratios:
            back_ratios = back_order_ratios
        
        front_std = np.std(front_ratios)
        middle_std = np.std(middle_ratios)
        back_std = np.std(back_ratios)
        
        print("\n1. 预售期订单分布一致性分析:")
        print("-" * 50)
        print(f"• 前10%时间段订单占比: {avg_front_ratio:.1f}% ± {front_std:.1f}% (标准差)")
        print(f"• 中间80%时间段订单占比: {np.mean(middle_ratios):.1f}% ± {middle_std:.1f}% (标准差)")
        print(f"• 后10%时间段订单占比: {avg_back_ratio:.1f}% ± {back_std:.1f}% (标准差)")
        
        # 判断一致性
        consistency_threshold = 5.0  # 标准差阈值
        consistent_periods = []
        if front_std < consistency_threshold:
            consistent_periods.append("前期")
        if middle_std < consistency_threshold:
            consistent_periods.append("中期")
        if back_std < consistency_threshold:
            consistent_periods.append("后期")
        
        if len(consistent_periods) >= 2:
            print(f"\n• 规律性发现: {'/'.join(consistent_periods)}订单分布具有高度一致性 (标准差<{consistency_threshold}%)")
            print(f"• 可预测性: 强 - 可作为CM2预测的可靠特征")
        else:
            print(f"\n• 规律性发现: 各车型预售期订单分布存在较大差异")
            print(f"• 可预测性: 中等 - 需结合其他特征进行CM2预测")
        
        # 分析锁单率一致性
        front_lock_rates_from_data = [data['front_10_lock_rate'] for data in date_analysis_results.values() if 'front_10_lock_rate' in data]
        back_lock_rates_from_data = [data['back_10_lock_rate'] for data in date_analysis_results.values() if 'back_10_lock_rate' in data]
        
        # 如果没有找到这些键，使用已计算的值
        if not front_lock_rates_from_data:
            front_lock_rates_analysis = front_lock_rates
        else:
            front_lock_rates_analysis = front_lock_rates_from_data
            
        if not back_lock_rates_from_data:
            back_lock_rates_analysis = back_lock_rates
        else:
            back_lock_rates_analysis = back_lock_rates_from_data
        
        front_lock_std = np.std(front_lock_rates_analysis)
        back_lock_std = np.std(back_lock_rates_analysis)
        
        print("\n2. 预售期锁单率一致性分析:")
        print("-" * 50)
        print(f"• 前10%时间段锁单率: {avg_front_lock:.1f}% ± {front_lock_std:.1f}% (标准差)")
        print(f"• 后10%时间段锁单率: {avg_back_lock:.1f}% ± {back_lock_std:.1f}% (标准差)")
        
        lock_consistency_threshold = 8.0
        if front_lock_std < lock_consistency_threshold and back_lock_std < lock_consistency_threshold:
            print(f"\n• 规律性发现: 锁单率时间分布具有高度一致性")
            print(f"• 转化规律: 各车型在预售不同阶段的转化表现相对稳定")
        else:
            print(f"\n• 规律性发现: 锁单率时间分布存在车型差异")
            print(f"• 转化规律: 不同车型的转化时机存在个性化特征")
        
        # 预售周期长度对比分析
        presale_lengths = {}
        for vehicle in ['CM0', 'CM1', 'DM0', 'DM1']:
            if vehicle in presale_periods:
                start_date = pd.to_datetime(presale_periods[vehicle]['start'])
                end_date = pd.to_datetime(presale_periods[vehicle]['end'])
                length = (end_date - start_date).days + 1
                presale_lengths[vehicle] = length
        
        print("\n3. 预售周期长度影响分析:")
        print("-" * 50)
        for vehicle, length in presale_lengths.items():
            print(f"• {vehicle}: {length}天预售期")
        
        if len(set(presale_lengths.values())) == 1:
            print(f"\n• 周期规律: 所有车型预售周期完全一致 ({list(presale_lengths.values())[0]}天)")
        else:
            avg_length = np.mean(list(presale_lengths.values()))
            length_std = np.std(list(presale_lengths.values()))
            print(f"\n• 周期规律: 平均预售周期{avg_length:.1f}天 ± {length_std:.1f}天")
            if length_std < 5:
                print(f"• 周期一致性: 高 - 预售周期相对稳定")
            else:
                print(f"• 周期一致性: 中等 - 预售周期存在差异")
        
        # CM2预测的关键规律总结
        print("\n4. CM2预测关键规律总结:")
        print("-" * 50)
        
        key_patterns = []
        if len(consistent_periods) >= 2:
            key_patterns.append(f"订单分布时间规律稳定({'/'.join(consistent_periods)})")
        
        if front_lock_std < lock_consistency_threshold and back_lock_std < lock_consistency_threshold:
            key_patterns.append("锁单率时间分布规律稳定")
        
        if abs(avg_front_ratio - avg_back_ratio) > 10:
            dominant_period = "前期" if avg_front_ratio > avg_back_ratio else "后期"
            key_patterns.append(f"预售{dominant_period}订单集中效应明显")
        
        if abs(avg_front_lock - avg_back_lock) > 5:
            better_lock_period = "前期" if avg_front_lock > avg_back_lock else "后期"
            key_patterns.append(f"预售{better_lock_period}转化效果更佳")
        
        if key_patterns:
            print("• 可用于CM2预测的稳定规律:")
            for i, pattern in enumerate(key_patterns, 1):
                print(f"  {i}. {pattern}")
            print(f"\n• 预测可信度: {'高' if len(key_patterns) >= 3 else '中等' if len(key_patterns) >= 2 else '较低'}")
        else:
            print("• 各车型预售日期特征差异较大，建议结合其他维度特征进行CM2预测")
    
    return {
        'date_analysis_results': date_analysis_results,
        'presale_periods': presale_periods,
        'consistency_analysis': {
            'order_distribution_consistency': front_std < consistency_threshold and back_std < consistency_threshold,
            'lock_rate_consistency': front_lock_std < lock_consistency_threshold and back_lock_std < lock_consistency_threshold,
            'key_patterns': key_patterns if 'key_patterns' in locals() else []
        }
    }

def analyze_order_hour_features(df):
    """
    分析模块8：下订时间（小时）特征分析
    
    Args:
        df (DataFrame): 包含订单数据的DataFrame
    """
    print("\n" + "="*60)
    print("分析模块8：下订时间（小时）特征分析")
    print("="*60)
    
    # 筛选出CM0、CM1、DM0、DM1车型
    target_vehicles = ['CM0', 'CM1', 'DM0', 'DM1']
    df_filtered = df[df['车型分组'].isin(target_vehicles)].copy()
    
    # 检查是否有Intention Payment Time 小时字段
    if 'Intention Payment Time 小时' not in df_filtered.columns:
        print("\n错误: 未找到'Intention Payment Time 小时'字段")
        return {}
    
    print("\n各车型24小时下订时间分布分析:")
    print("="*60)
    
    hour_analysis_results = {}
    
    for vehicle in target_vehicles:
        vehicle_data = df_filtered[df_filtered['车型分组'] == vehicle].copy()
        
        if len(vehicle_data) == 0:
            print(f"\n{vehicle}车型: 无订单数据")
            continue
        
        # 按小时分组统计
        hourly_stats = vehicle_data.groupby('Intention Payment Time 小时', observed=False).agg({
            'Order Number': 'count',
            'has_lock': ['sum', 'mean']
        }).round(4)
        
        hourly_stats.columns = ['订单数', '锁单数', '锁单率']
        hourly_stats['锁单率'] = hourly_stats['锁单率'] * 100
        hourly_stats = hourly_stats.reset_index()
        hourly_stats['订单占比(%)'] = (hourly_stats['订单数'] / hourly_stats['订单数'].sum() * 100).round(2)
        
        # 确保所有24小时都有数据（填充0）
        all_hours = pd.DataFrame({'Intention Payment Time 小时': range(24)})
        hourly_stats = all_hours.merge(hourly_stats, on='Intention Payment Time 小时', how='left').fillna(0)
        
        print(f"\n{vehicle}车型24小时订单分布:")
        print("-" * 70)
        print(f"{'小时':<6} {'订单数':<8} {'锁单数':<8} {'锁单率(%)':<12} {'订单占比(%)':<12}")
        print("-" * 70)
        
        for _, row in hourly_stats.iterrows():
            hour = int(row['Intention Payment Time 小时'])
            print(f"{hour:<6} {int(row['订单数']):<8} {int(row['锁单数']):<8} {row['锁单率']:<12.2f} {row['订单占比(%)']:<12.2f}")
        
        # 分析高峰时段
        top_hours = hourly_stats.nlargest(5, '订单数')
        print(f"\n{vehicle}车型订单高峰时段(TOP5):")
        print("-" * 50)
        for _, row in top_hours.iterrows():
            hour = int(row['Intention Payment Time 小时'])
            print(f"• {hour:02d}:00-{hour+1:02d}:00: {int(row['订单数'])}单 ({row['订单占比(%)']:.1f}%), 锁单率{row['锁单率']:.1f}%")
        
        # 分析锁单率高峰时段
        high_lock_hours = hourly_stats[hourly_stats['订单数'] > 0].nlargest(5, '锁单率')
        print(f"\n{vehicle}车型锁单率高峰时段(TOP5):")
        print("-" * 50)
        for _, row in high_lock_hours.iterrows():
            hour = int(row['Intention Payment Time 小时'])
            if row['订单数'] > 0:
                print(f"• {hour:02d}:00-{hour+1:02d}:00: 锁单率{row['锁单率']:.1f}% ({int(row['订单数'])}单)")
        
        # 保存分析结果
        hour_analysis_results[vehicle] = {
            'hourly_stats': hourly_stats,
            'total_orders': int(hourly_stats['订单数'].sum()),
            'peak_hours': top_hours['Intention Payment Time 小时'].tolist(),
            'high_lock_hours': high_lock_hours['Intention Payment Time 小时'].tolist()
        }
    
    # 跨车型对比分析
    print("\n\n" + "="*80)
    print("跨车型24小时下订时间特征对比分析")
    print("="*80)
    
    if len(hour_analysis_results) > 1:
        # 分析共同的高峰时段
        all_peak_hours = []
        for vehicle, data in hour_analysis_results.items():
            all_peak_hours.extend(data['peak_hours'][:3])  # 取每个车型的前3个高峰时段
        
        # 统计最常见的高峰时段
        from collections import Counter
        peak_hour_counts = Counter(all_peak_hours)
        common_peak_hours = peak_hour_counts.most_common(5)
        
        print("\n各车型共同高峰时段分析:")
        print("-" * 50)
        for hour, count in common_peak_hours:
            hour = int(hour)
            print(f"• {hour:02d}:00-{hour+1:02d}:00: {count}个车型的高峰时段")
            
            # 显示各车型在该时段的表现
            for vehicle, data in hour_analysis_results.items():
                hour_data = data['hourly_stats'][data['hourly_stats']['Intention Payment Time 小时'] == hour]
                if len(hour_data) > 0:
                    row = hour_data.iloc[0]
                    print(f"  - {vehicle}: {int(row['订单数'])}单 ({row['订单占比(%)']:.1f}%), 锁单率{row['锁单率']:.1f}%")
        
        # 分析时段特征
        print("\n24小时时段特征分析:")
        print("-" * 50)
        
        # 定义时段
        time_periods = {
            '深夜时段(0-6时)': list(range(0, 6)),
            '早晨时段(6-9时)': list(range(6, 9)),
            '上午时段(9-12时)': list(range(9, 12)),
            '下午时段(12-18时)': list(range(12, 18)),
            '晚上时段(18-22时)': list(range(18, 22)),
            '夜间时段(22-24时)': list(range(22, 24))
        }
        
        period_analysis = {}
        for period_name, hours in time_periods.items():
            period_stats = []
            
            for vehicle, data in hour_analysis_results.items():
                period_data = data['hourly_stats'][data['hourly_stats']['Intention Payment Time 小时'].isin(hours)]
                period_orders = period_data['订单数'].sum()
                period_lock_rate = (period_data['锁单数'].sum() / period_orders * 100) if period_orders > 0 else 0
                period_ratio = (period_orders / data['total_orders'] * 100) if data['total_orders'] > 0 else 0
                
                period_stats.append({
                    'vehicle': vehicle,
                    'orders': period_orders,
                    'lock_rate': period_lock_rate,
                    'ratio': period_ratio
                })
            
            # 计算该时段的平均表现
            avg_orders = np.mean([s['orders'] for s in period_stats])
            avg_lock_rate = np.mean([s['lock_rate'] for s in period_stats if s['orders'] > 0])
            avg_ratio = np.mean([s['ratio'] for s in period_stats])
            
            period_analysis[period_name] = {
                'avg_orders': avg_orders,
                'avg_lock_rate': avg_lock_rate,
                'avg_ratio': avg_ratio,
                'vehicle_stats': period_stats
            }
            
            print(f"\n{period_name}:")
            print(f"  平均订单数: {avg_orders:.1f}")
            print(f"  平均锁单率: {avg_lock_rate:.1f}%")
            print(f"  平均订单占比: {avg_ratio:.1f}%")
            
            # 显示各车型表现
            for stat in period_stats:
                if stat['orders'] > 0:
                    print(f"  - {stat['vehicle']}: {stat['orders']:.0f}单 ({stat['ratio']:.1f}%), 锁单率{stat['lock_rate']:.1f}%")
        
        # 找出最佳时段
        best_order_period = max(period_analysis.items(), key=lambda x: x[1]['avg_orders'])
        best_lock_period = max(period_analysis.items(), key=lambda x: x[1]['avg_lock_rate'] if not np.isnan(x[1]['avg_lock_rate']) else 0)
        
        print("\n时段特征总结:")
        print("-" * 50)
        print(f"• 订单量最高时段: {best_order_period[0]} (平均{best_order_period[1]['avg_orders']:.1f}单)")
        print(f"• 锁单率最高时段: {best_lock_period[0]} (平均{best_lock_period[1]['avg_lock_rate']:.1f}%)")
        
        # CM2预测建议
        print("\n\nCM2车型24小时营销策略建议:")
        print("-" * 50)
        
        # 基于历史数据的建议
        if best_order_period[1]['avg_ratio'] > 20:
            print(f"• 重点时段营销: {best_order_period[0]}是订单高峰期，建议加强该时段的营销投入")
        
        if best_lock_period[1]['avg_lock_rate'] > 30:
            print(f"• 锁单优化时段: {best_lock_period[0]}锁单率最高，建议在该时段优化转化流程")
        
        # 分析工作日vs非工作日特征（如果数据中有相关信息）
        print(f"• 全天候策略: 基于24小时分布特征，建议采用分时段差异化营销策略")
        
        # 推荐最佳投放时段
        top_3_periods = sorted(period_analysis.items(), key=lambda x: x[1]['avg_orders'], reverse=True)[:3]
        print(f"• 推荐投放时段排序:")
        for i, (period_name, data) in enumerate(top_3_periods, 1):
            print(f"  {i}. {period_name}: 平均{data['avg_orders']:.1f}单, 锁单率{data['avg_lock_rate']:.1f}%")
        
        # 深度规律性分析
        print("\n\n" + "="*80)
        print("跨车型24小时订单时间特征规律性深度解读")
        print("="*80)
        
        # 分析时段订单分布一致性
        print("\n1. 时段订单分布一致性分析:")
        print("-" * 50)
        
        period_consistency = {}
        for period_name, data in period_analysis.items():
            vehicle_ratios = [stat['ratio'] for stat in data['vehicle_stats']]
            ratio_std = np.std(vehicle_ratios)
            ratio_avg = np.mean(vehicle_ratios)
            
            period_consistency[period_name] = {
                'avg': ratio_avg,
                'std': ratio_std,
                'consistent': ratio_std < 3.0  # 3%标准差阈值
            }
            
            print(f"• {period_name}: {ratio_avg:.1f}% ± {ratio_std:.1f}% (标准差)")
        
        # 识别一致性时段
        consistent_periods = [name for name, data in period_consistency.items() if data['consistent']]
        
        if len(consistent_periods) >= 4:
            print(f"\n• 规律性发现: {len(consistent_periods)}/6个时段具有高度一致性")
            print(f"• 一致时段: {', '.join(consistent_periods)}")
            print(f"• 可预测性: 强 - 24小时分布规律稳定，可作为CM2预测的可靠特征")
        elif len(consistent_periods) >= 2:
            print(f"\n• 规律性发现: {len(consistent_periods)}/6个时段具有一致性")
            print(f"• 一致时段: {', '.join(consistent_periods)}")
            print(f"• 可预测性: 中等 - 部分时段规律稳定")
        else:
            print(f"\n• 规律性发现: 各车型24小时订单分布存在较大差异")
            print(f"• 可预测性: 较低 - 需结合其他特征进行CM2预测")
        
        # 分析峰值时段一致性
        print("\n2. 订单峰值时段一致性分析:")
        print("-" * 50)
        
        # 找出各车型的峰值时段
        vehicle_peak_periods = {}
        for vehicle, data in hour_analysis_results.items():
            vehicle_period_ratios = {}
            for period_name, period_data in period_analysis.items():
                vehicle_stat = next((s for s in period_data['vehicle_stats'] if s['vehicle'] == vehicle), None)
                if vehicle_stat:
                    vehicle_period_ratios[period_name] = vehicle_stat['ratio']
            
            # 找出该车型的峰值时段（订单占比最高的时段）
            if vehicle_period_ratios:
                peak_period = max(vehicle_period_ratios.items(), key=lambda x: x[1])
                vehicle_peak_periods[vehicle] = peak_period[0]
        
        # 统计峰值时段频率
        from collections import Counter
        peak_period_counts = Counter(vehicle_peak_periods.values())
        common_peak_periods = [period for period, count in peak_period_counts.items() if count >= 2]
        
        print(f"• 各车型峰值时段:")
        for vehicle, peak_period in vehicle_peak_periods.items():
            print(f"  {vehicle}: {peak_period}")
        
        if len(common_peak_periods) >= 1:
            print(f"\n• 共同峰值时段: {', '.join(common_peak_periods)} (出现在2个以上车型中)")
            print(f"• 峰值规律性: 强 - 存在明显的共同峰值时段")
        else:
            print(f"\n• 共同峰值时段: 无")
            print(f"• 峰值规律性: 弱 - 各车型峰值时段差异较大")
        
        # 分析锁单率时间分布一致性
        print("\n3. 时段锁单率分布一致性分析:")
        print("-" * 50)
        
        lock_rate_consistency = {}
        for period_name, data in period_analysis.items():
            vehicle_lock_rates = [stat['lock_rate'] for stat in data['vehicle_stats'] if stat['orders'] > 0]
            if vehicle_lock_rates:
                lock_std = np.std(vehicle_lock_rates)
                lock_avg = np.mean(vehicle_lock_rates)
                
                lock_rate_consistency[period_name] = {
                    'avg': lock_avg,
                    'std': lock_std,
                    'consistent': lock_std < 8.0  # 8%标准差阈值
                }
                print(f"• {period_name}锁单率: {lock_avg:.1f}% ± {lock_std:.1f}% (标准差)")
        
        consistent_lock_periods = [name for name, data in lock_rate_consistency.items() if data['consistent']]
        
        if len(consistent_lock_periods) >= 3:
            print(f"\n• 锁单率规律性: 强 - {len(consistent_lock_periods)}/6个时段锁单率分布一致")
            print(f"• 一致时段: {', '.join(consistent_lock_periods)}")
        else:
            print(f"\n• 锁单率规律性: 中等 - 各车型锁单率时间分布存在差异")
        
        # 工作时间vs非工作时间规律分析
        print("\n4. 工作时间vs非工作时间订单规律分析:")
        print("-" * 50)
        
        work_periods = ['早晨时段(6-9时)', '上午时段(9-12时)', '下午时段(12-18时)']
        non_work_periods = ['深夜时段(0-6时)', '晚上时段(18-22时)', '夜间时段(22-24时)']
        
        work_vs_nonwork_patterns = {}
        for vehicle, data in hour_analysis_results.items():
            work_ratio = sum(period_analysis[period]['vehicle_stats'][i]['ratio'] 
                           for period in work_periods 
                           for i, stat in enumerate(period_analysis[period]['vehicle_stats']) 
                           if stat['vehicle'] == vehicle)
            
            non_work_ratio = sum(period_analysis[period]['vehicle_stats'][i]['ratio'] 
                               for period in non_work_periods 
                               for i, stat in enumerate(period_analysis[period]['vehicle_stats']) 
                               if stat['vehicle'] == vehicle)
            
            work_vs_nonwork_patterns[vehicle] = {
                'work_ratio': work_ratio,
                'non_work_ratio': non_work_ratio,
                'work_dominant': work_ratio > non_work_ratio
            }
        
        work_dominant_count = sum(1 for data in work_vs_nonwork_patterns.values() if data['work_dominant'])
        total_vehicles = len(work_vs_nonwork_patterns)
        
        print(f"• 各车型工作时间vs非工作时间订单分布:")
        for vehicle, data in work_vs_nonwork_patterns.items():
            dominant = "工作时间" if data['work_dominant'] else "非工作时间"
            print(f"  {vehicle}: 工作时间{data['work_ratio']:.1f}% vs 非工作时间{data['non_work_ratio']:.1f}% (偏好{dominant})")
        
        if work_dominant_count == total_vehicles:
            print(f"\n• 时间偏好规律: 所有车型均偏好工作时间下单")
            print(f"• 规律一致性: 强 - 可作为CM2预测的稳定特征")
        elif work_dominant_count == 0:
            print(f"\n• 时间偏好规律: 所有车型均偏好非工作时间下单")
            print(f"• 规律一致性: 强 - 可作为CM2预测的稳定特征")
        else:
            print(f"\n• 时间偏好规律: {work_dominant_count}/{total_vehicles}车型偏好工作时间")
            print(f"• 规律一致性: 中等 - 存在车型差异")
        
        # CM2预测的关键时间规律总结
        print("\n5. CM2预测关键时间规律总结:")
        print("-" * 50)
        
        time_patterns = []
        
        if len(consistent_periods) >= 4:
            time_patterns.append(f"24小时分布规律高度稳定({len(consistent_periods)}/6时段一致)")
        elif len(consistent_periods) >= 2:
            time_patterns.append(f"24小时分布规律部分稳定({len(consistent_periods)}/6时段一致)")
        
        if len(common_peak_periods) >= 1:
            time_patterns.append(f"存在共同峰值时段({', '.join(common_peak_periods)})")
        
        if len(consistent_lock_periods) >= 3:
            time_patterns.append(f"锁单率时间分布规律稳定({len(consistent_lock_periods)}/6时段一致)")
        
        if work_dominant_count == total_vehicles or work_dominant_count == 0:
            preference = "工作时间" if work_dominant_count == total_vehicles else "非工作时间"
            time_patterns.append(f"统一偏好{preference}下单")
        
        if time_patterns:
            print("• 可用于CM2预测的稳定时间规律:")
            for i, pattern in enumerate(time_patterns, 1):
                print(f"  {i}. {pattern}")
            
            reliability_score = len(time_patterns)
            if reliability_score >= 3:
                reliability = "高"
            elif reliability_score >= 2:
                reliability = "中等"
            else:
                reliability = "较低"
            
            print(f"\n• 时间特征预测可信度: {reliability}")
            
            if reliability in ["高", "中等"]:
                print(f"• CM2营销建议: 可基于历史时间规律制定精准的时段营销策略")
                if len(common_peak_periods) >= 1:
                    print(f"• 重点时段: 优先在{', '.join(common_peak_periods)}投入营销资源")
            else:
                print(f"• CM2营销建议: 建议结合其他特征维度，避免过度依赖时间规律")
        else:
            print("• 各车型24小时订单特征差异较大，时间维度预测价值有限")
            print("• 建议重点关注其他特征维度进行CM2预测")
    
    return {
        'hour_analysis_results': hour_analysis_results,
        'time_periods': time_periods if 'time_periods' in locals() else {},
        'period_analysis': period_analysis if 'period_analysis' in locals() else {},
        'time_consistency_analysis': {
            'period_consistency': period_consistency if 'period_consistency' in locals() else {},
            'peak_consistency': len(common_peak_periods) >= 1 if 'common_peak_periods' in locals() else False,
            'lock_rate_consistency': len(consistent_lock_periods) >= 3 if 'consistent_lock_periods' in locals() else False,
            'time_patterns': time_patterns if 'time_patterns' in locals() else []
        }
    }

def analyze_leads_conversion_rate(df):
    """
    分析模块9：线索-订单转化率分析
    
    Args:
        df (DataFrame): 包含订单数据的DataFrame
    """
    print("\n" + "="*60)
    print("分析模块7：线索-订单转化率分析")
    print("="*60)
    
    try:
        # 定义各车型预售时间范围
        presale_periods = {
            'CM0': {'start': '2023-08-25', 'end': '2023-10-12'},
            'DM0': {'start': '2024-04-08', 'end': '2024-05-13'},
            'CM1': {'start': '2024-08-30', 'end': '2024-09-26'},
            'CM2': {'start': '2025-08-15', 'end': '2025-09-10'},
            'DM1': {'start': '2025-04-18', 'end': '2025-05-13'}
        }
        
        # 读取线索数据
        leads_df = pd.read_parquet('/Users/zihao_/Documents/github/W33_utils_3/data/leads_structure_analysis.parquet')
        print(f"线索数据加载成功，数据形状: {leads_df.shape}")
        
        # 确保时间字段为datetime类型
        leads_df['日(lc_create_time)'] = pd.to_datetime(leads_df['日(lc_create_time)'])
        df['Intention_Payment_Time'] = pd.to_datetime(df['Intention_Payment_Time'])
        
        print("\n各车型预售发布会后3日数据筛选:")
        print("-" * 50)
        
        # 为每个车型筛选预售前3日的数据
        vehicle_data = {}
        for vehicle, period in presale_periods.items():
            presale_start = pd.to_datetime(period['start'])
            # 预售发布会后3日：预售开始日期到预售开始日期后2天
            filter_start = presale_start
            filter_end = presale_start + pd.Timedelta(days=2)
            
            # 筛选该时间段的线索数据（线索数据没有车型分组字段）
            vehicle_leads = leads_df[
                (leads_df['日(lc_create_time)'] >= filter_start) & 
                (leads_df['日(lc_create_time)'] <= filter_end)
            ].copy()
            
            # 筛选该车型在预售前3日的订单数据
            vehicle_orders = df[
                (df['Intention_Payment_Time'] >= filter_start) & 
                (df['Intention_Payment_Time'] <= filter_end) &
                (df['车型分组'] == vehicle)
            ].copy()
            
            vehicle_data[vehicle] = {
                'leads': vehicle_leads,
                'orders': vehicle_orders,
                'period': f"{filter_start.strftime('%Y-%m-%d')} 到 {filter_end.strftime('%Y-%m-%d')}"
            }
            
            print(f"• {vehicle}: {vehicle_data[vehicle]['period']} (线索: {len(vehicle_leads)}, 订单: {len(vehicle_orders)})")
        
        # 合并所有车型的数据用于整体分析
        all_leads = pd.concat([data['leads'] for data in vehicle_data.values()], ignore_index=True)
        all_orders = pd.concat([data['orders'] for data in vehicle_data.values()], ignore_index=True)
        
        print(f"\n合并后数据: 线索 {len(all_leads)}, 订单 {len(all_orders)}")
        
        # 定义渠道映射关系（线索渠道 -> 订单渠道）
        channel_mapping = {
            '官网': '官网',
            '官方直播': '官方直播', 
            '活动': '活动',
            '活动（门店）': '门店活动',
            '经销商矩阵': '经销商',
            '门店投放': '门店投放',
            '门店自然客流': '门店自然',
            '内容运营': '内容运营',
            '平台运营': '平台运营',
            '投放': '投放',
            '网销': '网销',
            '网销平台': '网销平台',
            '微信生态': '微信',
            '线下投放': '线下投放',
            '新媒体': '新媒体',
            '异业合作': '异业合作',
            '展厅活动': '展厅活动',
            '自有渠道': '自有渠道'
        }
        
        # 计算各车型各渠道的线索总数
        vehicle_leads_totals = {}
        for vehicle, data in vehicle_data.items():
            vehicle_leads = data['leads']
            vehicle_leads_totals[vehicle] = {}
            
            for leads_channel, order_channel in channel_mapping.items():
                if leads_channel in vehicle_leads.columns:
                    total_leads = vehicle_leads[leads_channel].sum()
                    if pd.notna(total_leads) and total_leads > 0:
                        vehicle_leads_totals[vehicle][order_channel] = int(total_leads)
        
        print("\n各车型各渠道线索总数:")
        print("-" * 50)
        for vehicle in ['CM0', 'DM0', 'CM1', 'CM2', 'DM1']:
            if vehicle in vehicle_leads_totals:
                print(f"\n{vehicle}车型:")
                vehicle_totals = vehicle_leads_totals[vehicle]
                for channel, leads_count in sorted(vehicle_totals.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {channel:<15}: {leads_count:>8,} 条线索")
        
        # 按车型和渠道统计订单数（使用筛选后的数据）
        order_channel_analysis = all_orders.groupby(['车型分组', 'first_middle_channel_name'], observed=False).agg({
            'Order Number': 'count'
        }).reset_index()
        order_channel_analysis.rename(columns={'Order Number': 'order_count'}, inplace=True)
        
        # 计算转化率
        conversion_analysis = []
        
        for _, row in order_channel_analysis.iterrows():
            vehicle_type = row['车型分组']
            channel = row['first_middle_channel_name']
            order_count = row['order_count']
            
            # 查找对应车型的线索数
            leads_count = 0
            if vehicle_type in vehicle_leads_totals:
                leads_count = vehicle_leads_totals[vehicle_type].get(channel, 0)
            
            if leads_count > 0:
                conversion_rate = (order_count / leads_count) * 100
                leads_order_ratio = leads_count / order_count if order_count > 0 else float('inf')
                
                conversion_analysis.append({
                    '车型分组': vehicle_type,
                    '渠道': channel,
                    '线索数': leads_count,
                    '订单数': order_count,
                    '转化率(%)': round(conversion_rate, 2),
                    '线索订单比': round(leads_order_ratio, 2)
                })
        
        conversion_df = pd.DataFrame(conversion_analysis)
        
        if len(conversion_df) > 0:
            print("\n\n各车型各渠道转化率分析:")
            print("=" * 80)
            
            vehicle_types = sorted(conversion_df['车型分组'].unique())
            
            for vehicle in vehicle_types:
                vehicle_data = conversion_df[conversion_df['车型分组'] == vehicle].copy()
                vehicle_data = vehicle_data.sort_values('转化率(%)', ascending=False)
                
                print(f"\n{vehicle}车型渠道转化率排名:")
                print("-" * 70)
                print(f"{'渠道':<15} {'线索数':<10} {'订单数':<8} {'转化率(%)':<10} {'线索订单比':<10}")
                print("-" * 70)
                
                for _, row in vehicle_data.iterrows():
                    print(f"{row['渠道']:<15} {row['线索数']:<10,} {row['订单数']:<8} {row['转化率(%)']:<10} {row['线索订单比']:<10}")
            
            # CM2车型差异分析
            print("\n\n" + "="*80)
            print("CM2车型线索转化率差异解读")
            print("="*80)
            
            cm2_data = conversion_df[conversion_df['车型分组'] == 'CM2']
            target_vehicles = ['CM0', 'CM1', 'DM1']
            available_vehicles = [v for v in target_vehicles if v in conversion_df['车型分组'].unique()]
            
            if len(cm2_data) > 0 and len(available_vehicles) > 0:
                print("\n1. CM2车型渠道转化率特征:")
                print("-" * 50)
                
                cm2_avg_conversion = cm2_data['转化率(%)'].mean()
                cm2_avg_ratio = cm2_data['线索订单比'].mean()
                cm2_total_leads = cm2_data['线索数'].sum()
                cm2_total_orders = cm2_data['订单数'].sum()
                
                print(f"• 平均转化率: {cm2_avg_conversion:.2f}%")
                print(f"• 平均线索订单比: {cm2_avg_ratio:.2f}")
                print(f"• 总线索数: {cm2_total_leads:,}")
                print(f"• 总订单数: {cm2_total_orders:,}")
                
                # 找出CM2表现最好和最差的渠道
                cm2_sorted = cm2_data.sort_values('转化率(%)', ascending=False)
                if len(cm2_sorted) > 0:
                    best_channel = cm2_sorted.iloc[0]
                    worst_channel = cm2_sorted.iloc[-1]
                    
                    print(f"• 最佳转化渠道: {best_channel['渠道']} ({best_channel['转化率(%)']:.2f}%)")
                    print(f"• 最低转化渠道: {worst_channel['渠道']} ({worst_channel['转化率(%)']:.2f}%)")
                
                # 与其他车型对比
                print("\n2. 与其他车型对比分析:")
                print("-" * 50)
                
                for vehicle in available_vehicles:
                    other_data = conversion_df[conversion_df['车型分组'] == vehicle]
                    if len(other_data) > 0:
                        other_avg_conversion = other_data['转化率(%)'].mean()
                        other_avg_ratio = other_data['线索订单比'].mean()
                        
                        conversion_diff = cm2_avg_conversion - other_avg_conversion
                        ratio_diff = cm2_avg_ratio - other_avg_ratio
                        
                        print(f"\n相对{vehicle}车型:")
                        print(f"• 转化率差异: {conversion_diff:+.2f}个百分点")
                        print(f"• 线索订单比差异: {ratio_diff:+.2f}")
                        
                        # 分析共同渠道的差异
                        cm2_channels = set(cm2_data['渠道'])
                        other_channels = set(other_data['渠道'])
                        common_channels = cm2_channels & other_channels
                        
                        if common_channels:
                            print(f"• 共同渠道数: {len(common_channels)}")
                            
                            # 详细对比每个渠道的转化率和线索订单数据
                            channel_comparisons = []
                            for channel in common_channels:
                                cm2_channel_data = cm2_data[cm2_data['渠道'] == channel]
                                other_channel_data = other_data[other_data['渠道'] == channel]
                                
                                if len(cm2_channel_data) > 0 and len(other_channel_data) > 0:
                                    cm2_conv = cm2_channel_data['转化率(%)'].iloc[0]
                                    other_conv = other_channel_data['转化率(%)'].iloc[0]
                                    conv_diff = cm2_conv - other_conv
                                    
                                    cm2_leads = cm2_channel_data['线索数'].iloc[0]
                                    other_leads = other_channel_data['线索数'].iloc[0]
                                    leads_diff = cm2_leads - other_leads
                                    
                                    cm2_orders = cm2_channel_data['订单数'].iloc[0]
                                    other_orders = other_channel_data['订单数'].iloc[0]
                                    orders_diff = cm2_orders - other_orders
                                    
                                    cm2_ratio = cm2_channel_data['线索订单比'].iloc[0]
                                    other_ratio = other_channel_data['线索订单比'].iloc[0]
                                    ratio_diff = cm2_ratio - other_ratio
                                    
                                    channel_comparisons.append({
                                        'channel': channel,
                                        'cm2_conv': cm2_conv,
                                        'other_conv': other_conv,
                                        'conv_diff': conv_diff,
                                        'cm2_leads': cm2_leads,
                                        'other_leads': other_leads,
                                        'leads_diff': leads_diff,
                                        'cm2_orders': cm2_orders,
                                        'other_orders': other_orders,
                                        'orders_diff': orders_diff,
                                        'cm2_ratio': cm2_ratio,
                                        'other_ratio': other_ratio,
                                        'ratio_diff': ratio_diff
                                    })
                            
                            # 计算综合影响指标：线索数变化 × 转化率变化对订单数的影响
                            for comp in channel_comparisons:
                                # 计算订单数变化的两个组成部分
                                # 1. 线索数变化带来的订单数影响（保持原转化率）
                                leads_impact = comp['leads_diff'] * (comp['other_conv'] / 100)
                                # 2. 转化率变化带来的订单数影响（基于CM2线索数）
                                conv_impact = comp['cm2_leads'] * (comp['conv_diff'] / 100)
                                # 3. 综合影响
                                total_impact = leads_impact + conv_impact
                                
                                comp['leads_impact'] = leads_impact
                                comp['conv_impact'] = conv_impact
                                comp['total_impact'] = total_impact
                            
                            # 按综合影响排序，显示最重要的渠道差异
                            channel_comparisons.sort(key=lambda x: abs(x['total_impact']), reverse=True)
                            
                            print(f"• 主要渠道综合对比分析:")
                            print(f"  {'渠道':<15} {'线索差异':<8} {'转化率差异':<10} {'线索影响':<8} {'转化率影响':<10} {'综合影响':<8} {'实际订单差异':<10}")
                            print(f"  {'-'*110}")
                            
                            for comp in channel_comparisons[:8]:  # 显示前8个渠道
                                print(f"  {comp['channel']:<15} {comp['leads_diff']:+7d} {comp['conv_diff']:+8.2f}% {comp['leads_impact']:+7.1f} {comp['conv_impact']:+9.1f} {comp['total_impact']:+7.1f} {comp['orders_diff']:+9d}")
                            
                            # 分析最重要的渠道差异
                            print(f"\n• 关键渠道深度分析:")
                            for i, comp in enumerate(channel_comparisons[:5], 1):
                                impact_type = "正向" if comp['total_impact'] > 0 else "负向"
                                main_driver = "线索数量" if abs(comp['leads_impact']) > abs(comp['conv_impact']) else "转化率"
                                
                                print(f"\n  {i}. {comp['channel']} - {impact_type}影响 (预期订单影响: {comp['total_impact']:+.1f})")
                                print(f"     • 线索数对比: CM2 {comp['cm2_leads']} vs {vehicle} {comp['other_leads']} (差异: {comp['leads_diff']:+d})")
                                print(f"     • 转化率对比: CM2 {comp['cm2_conv']:.2f}% vs {vehicle} {comp['other_conv']:.2f}% (差异: {comp['conv_diff']:+.2f}%)")
                                print(f"     • 订单数对比: CM2 {comp['cm2_orders']} vs {vehicle} {comp['other_orders']} (实际差异: {comp['orders_diff']:+d})")
                                print(f"     • 主要驱动因素: {main_driver} (线索影响: {comp['leads_impact']:+.1f}, 转化率影响: {comp['conv_impact']:+.1f})")
                                
                                # 策略建议
                                if comp['total_impact'] > 5:
                                    if comp['leads_diff'] > 0 and comp['conv_diff'] > 0:
                                        print(f"     • 策略建议: 优势渠道，建议保持并扩大投入")
                                    elif comp['leads_diff'] > 0 and comp['conv_diff'] < 0:
                                        print(f"     • 策略建议: 线索量优势明显，但需优化转化流程")
                                    elif comp['leads_diff'] < 0 and comp['conv_diff'] > 0:
                                        print(f"     • 策略建议: 转化效率高，建议增加线索投入")
                                elif comp['total_impact'] < -5:
                                    print(f"     • 策略建议: 需重点关注和改进的渠道")
                            
                            # 按不同维度分析渠道表现
                            print(f"\n• 渠道表现分类分析:")
                            
                            # 线索量优势渠道
                            high_lead_channels = [comp for comp in channel_comparisons if comp['leads_diff'] > 20]
                            if high_lead_channels:
                                high_lead_channels.sort(key=lambda x: x['leads_diff'], reverse=True)
                                print(f"\n  线索量优势渠道 (差异>20):")
                                for comp in high_lead_channels[:3]:
                                    efficiency = "高效" if comp['conv_diff'] > 0 else "待优化"
                                    print(f"  - {comp['channel']}: +{comp['leads_diff']}线索, 转化率{comp['conv_diff']:+.2f}% ({efficiency})")
                            
                            # 转化率优势渠道
                            high_conv_channels = [comp for comp in channel_comparisons if comp['conv_diff'] > 1.0]
                            if high_conv_channels:
                                high_conv_channels.sort(key=lambda x: x['conv_diff'], reverse=True)
                                print(f"\n  转化率优势渠道 (差异>1.0%):")
                                for comp in high_conv_channels[:3]:
                                    volume = "高量" if comp['leads_diff'] > 0 else "低量"
                                    print(f"  - {comp['channel']}: +{comp['conv_diff']:.2f}%转化率, 线索{comp['leads_diff']:+d} ({volume})")
                            
                            # 综合优势渠道
                            best_channels = [comp for comp in channel_comparisons if comp['total_impact'] > 5]
                            if best_channels:
                                best_channels.sort(key=lambda x: x['total_impact'], reverse=True)
                                print(f"\n  综合优势渠道 (预期订单影响>5):")
                                for comp in best_channels[:3]:
                                    print(f"  - {comp['channel']}: 预期+{comp['total_impact']:.1f}订单 (线索{comp['leads_diff']:+d}, 转化率{comp['conv_diff']:+.2f}%)")
                            
                            # 需改进渠道
                            weak_channels = [comp for comp in channel_comparisons if comp['total_impact'] < -3]
                            if weak_channels:
                                weak_channels.sort(key=lambda x: x['total_impact'])
                                print(f"\n  需改进渠道 (预期订单影响<-3):")
                                for comp in weak_channels[:3]:
                                    main_issue = "线索不足" if comp['leads_diff'] < -10 else "转化率低" if comp['conv_diff'] < -1 else "综合表现差"
                                    print(f"  - {comp['channel']}: 预期{comp['total_impact']:.1f}订单 ({main_issue})")
                        
                        # 分析CM2独有和其他车型独有的渠道
                        cm2_unique = cm2_channels - other_channels
                        if cm2_unique:
                            cm2_unique_data = cm2_data[cm2_data['渠道'].isin(cm2_unique)]
                            cm2_unique_sorted = cm2_unique_data.sort_values('订单数', ascending=False)
                            print(f"\n• CM2独有渠道分析({len(cm2_unique)}个):")
                            total_unique_orders = cm2_unique_data['订单数'].sum()
                            total_unique_leads = cm2_unique_data['线索数'].sum()
                            avg_unique_conv = cm2_unique_data['转化率(%)'].mean()
                            print(f"  总体表现: {total_unique_orders}订单, {total_unique_leads}线索, 平均转化率{avg_unique_conv:.2f}%")
                            print(f"  主要渠道:")
                            for _, row in cm2_unique_sorted.head(3).iterrows():
                                print(f"  - {row['渠道']}: {row['订单数']}订单, {row['线索数']}线索, 转化率{row['转化率(%)']:.2f}%")
                        
                        other_unique = other_channels - cm2_channels
                        if other_unique:
                            other_unique_data = other_data[other_data['渠道'].isin(other_unique)]
                            other_unique_sorted = other_unique_data.sort_values('订单数', ascending=False)
                            print(f"\n• {vehicle}独有渠道分析({len(other_unique)}个):")
                            total_other_orders = other_unique_data['订单数'].sum()
                            total_other_leads = other_unique_data['线索数'].sum()
                            avg_other_conv = other_unique_data['转化率(%)'].mean()
                            print(f"  总体表现: {total_other_orders}订单, {total_other_leads}线索, 平均转化率{avg_other_conv:.2f}%")
                            print(f"  主要渠道:")
                            for _, row in other_unique_sorted.head(3).iterrows():
                                print(f"  - {row['渠道']}: {row['订单数']}订单, {row['线索数']}线索, 转化率{row['转化率(%)']:.2f}%")
                
                # 策略建议
                print("\n3. 转化率优化建议:")
                print("-" * 50)
                
                if cm2_avg_conversion > 5:
                    print("• CM2车型整体转化率较高，建议重点维护高转化渠道")
                elif cm2_avg_conversion < 2:
                    print("• CM2车型整体转化率偏低，建议优化线索质量和转化流程")
                else:
                    print("• CM2车型转化率适中，建议平衡线索获取和转化优化")
                
                # 渠道效率分析
                if len(cm2_sorted) > 1:
                    high_efficiency_channels = cm2_sorted[cm2_sorted['转化率(%)'] > cm2_avg_conversion]
                    if len(high_efficiency_channels) > 0:
                        print(f"• 高效渠道({len(high_efficiency_channels)}个): 建议加大投入")
                        for _, channel_data in high_efficiency_channels.head(3).iterrows():
                            print(f"  - {channel_data['渠道']}: {channel_data['转化率(%)']:.2f}%")
                    
                    low_efficiency_channels = cm2_sorted[cm2_sorted['转化率(%)'] < cm2_avg_conversion * 0.5]
                    if len(low_efficiency_channels) > 0:
                        print(f"• 低效渠道({len(low_efficiency_channels)}个): 建议优化或调整策略")
                        for _, channel_data in low_efficiency_channels.head(3).iterrows():
                            print(f"  - {channel_data['渠道']}: {channel_data['转化率(%)']:.2f}%")
            
            else:
                if len(cm2_data) == 0:
                    print("\n未找到CM2车型的转化数据")
                if len(available_vehicles) == 0:
                    print("\n未找到可对比的车型数据(CM0、CM1、DM1)")
            
            return {
                'conversion_analysis': conversion_df,
                'leads_channel_totals': vehicle_leads_totals,
                'channel_mapping': channel_mapping
            }
        
        else:
            print("\n警告: 未找到匹配的渠道数据，无法计算转化率")
            return {}
    
    except Exception as e:
        print(f"\n错误: 线索转化率分析失败 - {e}")
        return {}

def comprehensive_analysis(df):
    """
    综合分析函数
    
    Args:
        df (DataFrame): 原始数据
    """
    # 1. 计算锁单率指标
    df = calculate_lock_rate_indicator(df)
    
    # 2. 车型结构分析
    vehicle_analysis = analyze_by_vehicle_type(df)
    
    # 3. 人口统计学特征分析
    demographics_analysis = analyze_by_demographics(df)
    
    # 4. 地理位置分析
    geographic_analysis = analyze_by_geography(df)
    
    # 5. 线索渠道分析
    channel_analysis = analyze_by_channel(df)
    
    # 6. 下订日期特征分析
    date_features_analysis = analyze_order_date_features(df)
    
    # 7. 下订时间（小时）特征分析
    hour_features_analysis = analyze_order_hour_features(df)
    
    # 8. 线索转化率分析
    conversion_analysis = analyze_leads_conversion_rate(df)
    
    return {
        'vehicle_analysis': vehicle_analysis,
        'demographics_analysis': demographics_analysis,
        'geographic_analysis': geographic_analysis,
        'channel_analysis': channel_analysis,
        'date_features_analysis': date_features_analysis,
        'hour_features_analysis': hour_features_analysis,
        'conversion_analysis': conversion_analysis
    }

def main():
    """
    主函数
    """
    # 文件路径
    file_path = "/Users/zihao_/Documents/github/W33_utils_3/data/intention_order_analysis.parquet"
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    # 读取数据
    df = analyze_parquet_data(file_path)
    
    if df is not None:
        # 进行综合分析
        df_analyzed = comprehensive_analysis(df)
        print("\n" + "="*60)
        print("所有分析完成！")
        print("="*60)
    else:
        print("\n分析失败！")

if __name__ == "__main__":
    main()