#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量查询模块 - 基于乘用车上险量数据的多维度销量查询

支持自然语言查询转换为SQL查询，提供灵活的销量数据分析能力。
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Template
import re
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from .base_module import BaseAnalysisModule
from llm.glm import GLMClient, get_glm_client
from llm.prompts import AI_INSIGHTS_GENERATION_PROMPT, SALES_QUERY_PARAMETER_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class SalesQueryModule(BaseAnalysisModule):
    """销量查询模块
    
    基于乘用车上险量数据的多维度销量查询模块，支持：
    - 品牌销量查询
    - 时间趋势分析
    - 地区销量统计
    - 多维度组合查询
    - 自然语言参数提取
    """
    
    # 模块基本信息
    module_id = "sales_query"
    module_name = "销量查询模块"
    description = "基于乘用车上险量数据的多维度销量查询模块"
    
    # 数据库感知能力
    supported_databases = ["parquet", "duckdb", "pandas"]
    required_fields = ["sales_volume", "date"]
    optional_fields = [
        "brand", "model_name", "province", "city", 
        "fuel_type", "body_style", "is_luxury_brand", "city_tier"
    ]
    
    def __init__(self):
        """初始化销量查询模块"""
        super().__init__()
        self.query_templates = self._load_query_templates()
        self.brand_mapping = self._load_brand_mapping()
        self.region_mapping = self._load_region_mapping()
    
    def _load_query_templates(self) -> Dict[str, Any]:
        """加载查询模板"""
        return {
            "brand_sales": {
                "name": "品牌销量查询",
                "description": "查询指定品牌的销量数据",
                "template": """
                SELECT 
                    brand,
                    {% if model_names %}model_name,{% endif %}
                    SUM(sales_volume) as total_sales,
                    COUNT(*) as record_count,
                    AVG(sales_volume) as avg_sales
                FROM data 
                WHERE 1=1
                {% if brands %}
                    AND brand IN ({{ brands | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if model_names %}
                    AND model_name IN ({{ model_names | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if start_date %}
                    AND date >= '{{ start_date }}'
                {% endif %}
                {% if end_date %}
                    AND date <= '{{ end_date }}'
                {% endif %}
                GROUP BY brand{% if model_names %}, model_name{% endif %}
                ORDER BY total_sales DESC
                {% if limit %}
                    LIMIT {{ limit }}
                {% endif %}
                """,
                "required_params": [],
                "optional_params": ["brands", "model_names", "start_date", "end_date", "limit"],
                "result_columns": ["brand", "total_sales", "record_count", "avg_sales"]
            },
            "time_trend": {
                "name": "时间趋势查询",
                "description": "查询销量的时间趋势",
                "template": """
                SELECT 
                    date,
                    SUM(sales_volume) as total_sales,
                    COUNT(DISTINCT brand) as brand_count
                FROM data 
                WHERE 1=1
                {% if brands %}
                    AND brand IN ({{ brands | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if start_date %}
                    AND date >= '{{ start_date }}'
                {% endif %}
                {% if end_date %}
                    AND date <= '{{ end_date }}'
                {% endif %}
                GROUP BY date
                ORDER BY date
                """,
                "required_params": [],
                "optional_params": ["brands", "start_date", "end_date"],
                "result_columns": ["date", "total_sales", "brand_count"]
            },
            "region_sales": {
                "name": "地区销量查询",
                "description": "查询指定地区的销量数据",
                "template": """
                SELECT 
                    province,
                    city,
                    {% if brands %}brand,{% endif %}
                    {% if model_names %}model_name,{% endif %}
                    SUM(sales_volume) as total_sales,
                    COUNT(DISTINCT brand) as brand_count
                FROM data 
                WHERE 1=1
                {% if provinces %}
                    AND province IN ({{ provinces | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if cities %}
                    AND city IN ({{ cities | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if brands %}
                    AND brand IN ({{ brands | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if model_names %}
                    AND model_name IN ({{ model_names | map('tojsonfilter') | join(', ') }})
                {% endif %}
                GROUP BY province, city{% if brands %}, brand{% endif %}{% if model_names %}, model_name{% endif %}
                ORDER BY total_sales DESC
                {% if limit %}
                    LIMIT {{ limit }}
                {% endif %}
                """,
                "required_params": [],
                "optional_params": ["provinces", "cities", "brands", "model_names", "limit"],
                "result_columns": ["province", "city", "total_sales", "brand_count"]
            },
            "fuel_type_analysis": {
                "name": "燃料类型分析",
                "description": "按燃料类型分析销量",
                "template": """
                SELECT 
                    fuel_type,
                    {% if brands %}brand,{% endif %}
                    {% if model_names %}model_name,{% endif %}
                    SUM(sales_volume) as total_sales,
                    COUNT(DISTINCT brand) as brand_count,
                    AVG(sales_volume) as avg_sales
                FROM data 
                WHERE 1=1
                {% if fuel_types %}
                    AND fuel_type IN ({{ fuel_types | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if brands %}
                    AND brand IN ({{ brands | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if model_names %}
                    AND model_name IN ({{ model_names | map('tojsonfilter') | join(', ') }})
                {% endif %}
                GROUP BY fuel_type{% if brands %}, brand{% endif %}{% if model_names %}, model_name{% endif %}
                ORDER BY total_sales DESC
                """,
                "required_params": [],
                "optional_params": ["fuel_types", "brands", "model_names"],
                "result_columns": ["fuel_type", "total_sales", "brand_count", "avg_sales"]
            },
            "model_sales": {
                "name": "车型销量查询",
                "description": "查询指定车型的销量数据",
                "template": """
                SELECT 
                    brand,
                    model_name,
                    SUM(sales_volume) as total_sales,
                    COUNT(*) as record_count,
                    AVG(sales_volume) as avg_sales
                FROM data 
                WHERE 1=1
                {% if brands %}
                    AND brand IN ({{ brands | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if model_names %}
                    AND model_name IN ({{ model_names | map('tojsonfilter') | join(', ') }})
                {% endif %}
                {% if start_date %}
                    AND date >= '{{ start_date }}'
                {% endif %}
                {% if end_date %}
                    AND date <= '{{ end_date }}'
                {% endif %}
                GROUP BY brand, model_name
                ORDER BY total_sales DESC
                {% if limit %}
                    LIMIT {{ limit }}
                {% endif %}
                """,
                "required_params": [],
                "optional_params": ["brands", "model_names", "start_date", "end_date", "limit"],
                "result_columns": ["brand", "model_name", "total_sales", "record_count", "avg_sales"]
            },
            "general_sales": {
                "name": "综合销量查询",
                "description": "通用销量查询模板",
                "template": """
                SELECT 
                    brand,
                    SUM(sales_volume) as total_sales
                FROM data 
                GROUP BY brand
                ORDER BY total_sales DESC
                LIMIT 10
                """,
                "required_params": [],
                "optional_params": [],
                "result_columns": ["brand", "total_sales"]
            }
        }
    
    def _load_brand_mapping(self) -> Dict[str, str]:
        """加载品牌映射表"""
        return {
            "特斯拉": "Tesla",
            "比亚迪": "BYD",
            "蔚来": "NIO",
            "小鹏": "XPENG",
            "理想": "Li Auto",
            "智己": "IM Motors",
            "智界": "AITO",
            "极氪": "Zeekr",
            "极狐": "ARCFOX",
            "岚图": "Voyah",
            "阿维塔": "AVATR",
            "深蓝": "Deepal",
            "问界": "AITO",
            "奔驰": "Mercedes-Benz",
            "宝马": "BMW",
            "奥迪": "Audi",
            "大众": "Volkswagen",
            "丰田": "Toyota",
            "本田": "Honda",
            "日产": "Nissan",
            "现代": "Hyundai",
            "起亚": "KIA",
            "沃尔沃": "Volvo",
            "捷豹": "Jaguar",
            "路虎": "Land Rover",
            "保时捷": "Porsche",
            "法拉利": "Ferrari",
            "玛莎拉蒂": "Maserati",
            "宾利": "Bentley",
            "劳斯莱斯": "Rolls-Royce"
        }
    
    def _load_region_mapping(self) -> Dict[str, str]:
        """加载地区映射表"""
        return {
            "北京": "北京市",
            "上海": "上海市",
            "广州": "广东省",
            "深圳": "广东省",
            "杭州": "浙江省",
            "南京": "江苏省",
            "成都": "四川省",
            "重庆": "重庆市",
            "西安": "陕西省",
            "武汉": "湖北省"
        }
    
    def prepare_data(self, db_connector: Any, params: Dict[str, Any]) -> pd.DataFrame:
        """准备数据
        
        Args:
            db_connector: 数据库连接器（暂时不使用）
            params: 参数字典
            
        Returns:
            pandas.DataFrame: 加载的数据
        """
        try:
            # 获取数据源路径
            data_source = params.get('data_source', 'data/乘用车上险量_0723.parquet')
            
            # 如果是相对路径，转换为绝对路径
            if not Path(data_source).is_absolute():
                project_root = Path(__file__).parent.parent
                data_source = project_root / data_source
            
            logger.info(f"加载数据源: {data_source}")
            
            # 加载parquet文件
            if Path(data_source).exists():
                df = pd.read_parquet(data_source)
                logger.info(f"数据加载成功，形状: {df.shape}")
                return df
            else:
                raise FileNotFoundError(f"数据文件不存在: {data_source}")
                
        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            raise
    
    def run(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行查询
        
        Args:
            data: 准备好的数据
            params: 查询参数
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        try:
            # 1. 提取查询参数
            extracted_params = self._extract_query_parameters(params)
            
            # 2. 选择查询模板
            template_info = self._select_template(extracted_params)
            
            # 3. 构建并执行查询
            result_df = self._execute_query(data, template_info, extracted_params)
            
            # 4. 格式化结果
            result = self._format_results(result_df, template_info, extracted_params)
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return {
                "success": False,
                "data": [],
                "analysis": {"error": str(e)},
                "visualization": {},
                "insights": [f"查询执行失败: {str(e)}"]
            }
    
    def summarize(self, results: Dict[str, Any]) -> str:
        """生成查询结果摘要
        
        Args:
            results: 查询结果
            
        Returns:
            str: 文字摘要
        """
        try:
            data = results.get('data', [])
            analysis = results.get('analysis', {})
            insights = results.get('insights', [])
            
            if not data:
                return "查询未返回任何结果。"
            
            # 构建结构化的返回结果
            summary_parts = []
            
            # 1. 查询结果概述
            data_summary = analysis.get('data_summary', {})
            if data_summary.get('sales_stats'):
                stats = data_summary['sales_stats']
                summary_parts.append(f"📊 查询结果：共找到 {len(data)} 条记录")
                summary_parts.append(f"💰 总销量：{stats['total']:,.0f} 辆")
                if len(data) > 1:
                    summary_parts.append(f"📈 平均销量：{stats['average']:,.0f} 辆")
                    summary_parts.append(f"🔝 最高销量：{stats['max']:,.0f} 辆")
            else:
                summary_parts.append(f"📊 查询结果：共找到 {len(data)} 条记录")
            
            # 2. 具体数据展示（前3条）
            if data:
                summary_parts.append("\n🔍 详细数据：")
                for i, item in enumerate(data[:3]):
                    if 'brand' in item and 'total_sales' in item:
                        if 'model_name' in item:
                            summary_parts.append(f"  {i+1}. {item['brand']} {item['model_name']}：{item['total_sales']:,.0f} 辆")
                        else:
                            summary_parts.append(f"  {i+1}. {item['brand']}：{item['total_sales']:,.0f} 辆")
                    elif 'province' in item and 'total_sales' in item:
                        city_info = f" {item['city']}" if item.get('city') else ""
                        summary_parts.append(f"  {i+1}. {item['province']}{city_info}：{item['total_sales']:,.0f} 辆")
                    elif 'fuel_type' in item and 'total_sales' in item:
                        summary_parts.append(f"  {i+1}. {item['fuel_type']}：{item['total_sales']:,.0f} 辆")
                    else:
                        # 通用格式
                        sales_value = item.get('total_sales', item.get('sales', 0))
                        summary_parts.append(f"  {i+1}. 销量：{sales_value:,.0f} 辆")
                
                if len(data) > 3:
                    summary_parts.append(f"  ... 还有 {len(data) - 3} 条记录")
            
            # 3. 洞察分析
            if insights:
                summary_parts.append("\n💡 数据洞察：")
                for insight in insights[:2]:  # 只显示前2个洞察
                    if insight and len(insight.strip()) > 0:
                        summary_parts.append(f"  • {insight.strip()}")
            
            return "\n".join(summary_parts)
                
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return f"查询完成，但摘要生成失败: {str(e)}"
    
    def _extract_query_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """从用户问题中提取查询参数（使用GLM智能提取）"""
        user_question = params.get('user_question', '')
        
        try:
            # 使用GLM进行智能参数提取
            glm_client = get_glm_client()
            prompt = SALES_QUERY_PARAMETER_EXTRACTION_PROMPT.format(user_question=user_question)
            extracted_params = glm_client.parse_json_response(prompt)
            
            # 如果GLM提取失败，使用备用的正则表达式方法
            if "error" in extracted_params:
                logger.warning(f"GLM参数提取失败，使用备用方法: {extracted_params}")
                return self._extract_query_parameters_fallback(user_question)
            
            # 标准化提取的参数
            extracted = {
                'user_question': user_question,
                'brands': extracted_params.get('brands', []),
                'model_names': extracted_params.get('model_names', []),
                'provinces': extracted_params.get('provinces', []),
                'cities': extracted_params.get('cities', []),
                'fuel_types': extracted_params.get('fuel_types', []),
                'start_date': extracted_params.get('start_date'),
                'end_date': extracted_params.get('end_date'),
                'limit': extracted_params.get('limit'),
                'time_granularity': extracted_params.get('time_granularity', 'year')
            }
            
            # 清理车型名称中的品牌前缀
            extracted = self._clean_model_names(extracted)
            
            logger.info(f"GLM参数提取成功: {extracted}")
            return extracted
            
        except Exception as e:
            logger.error(f"GLM参数提取异常: {e}，使用备用方法")
            return self._extract_query_parameters_fallback(params)
    
    def _extract_query_parameters_fallback(self, params) -> Dict[str, Any]:
        """备用的正则表达式参数提取方法"""
        # 处理参数类型
        if isinstance(params, str):
            user_question = params
        elif isinstance(params, dict):
            user_question = params.get('user_question', '')
        else:
            user_question = str(params)
        extracted = {
            'user_question': user_question,
            'brands': [],
            'model_names': [],
            'provinces': [],
            'cities': [],
            'fuel_types': [],
            'start_date': None,
            'end_date': None,
            'limit': None,
            'time_granularity': 'year'
        }
        
        # 提取品牌信息
        for chinese_name, english_name in self.brand_mapping.items():
            if chinese_name in user_question or english_name.lower() in user_question.lower():
                extracted['brands'].append(chinese_name)
        
        # 提取车型信息（改进的正则表达式）
        model_patterns = [
            r'智己LS[67]|智己L[67]', # 智己LS6, 智己L7, 智己L6
            r'特斯拉Model\s*[XYZ3S]', # 特斯拉Model Y, 特斯拉Model 3
            r'Model\s*[XYZ3S]', # Model Y, Model 3
            r'宝马[X\d系]+', # 宝马X5, 宝马3系
            r'奔驰[A-Z\d级]+', # 奔驰C级, 奔驰E级
            r'比亚迪[汉唐宋元秦海豚海豹驱逐舰护卫舰]+',  # 比亚迪汉、比亚迪唐等
            r'蔚来ES[68]|蔚来ET[57]',    # 蔚来ES6、ES8, 蔚来ET5、ET7等
            r'理想ONE|理想L[789]',      # 理想ONE, 理想L7, 理想L8, 理想L9
            r'小鹏P[57]|小鹏G[39]',     # 小鹏P5、P7, 小鹏G3、G9等
        
        ]
        
        # 处理多个车型的情况
        # 1. 先用原方法在整个问题中查找
        for pattern in model_patterns:
            matches = re.findall(pattern, user_question)
            for match in matches:
                if match not in extracted['model_names']:
                    extracted['model_names'].append(match)
        
        # 2. 再处理用分隔符连接的车型
        # 分割用户问题，提取所有可能的车型
        question_parts = re.split(r'[和、，,与及]', user_question)
        
        for part in question_parts:
            part = part.strip()
            for pattern in model_patterns:
                matches = re.findall(pattern, part)
                for match in matches:
                    if match not in extracted['model_names']:
                        extracted['model_names'].append(match)
        
        # 3. 特殊处理：手动识别一些常见的车型组合
        special_patterns = [
            r'Model\s*([A-Z0-9]+)',  # Model Y, Model 3等
            r'ES(\d+)',             # ES6, ES8等
            r'ET(\d+)',             # ET7, ET5等
        ]
        
        for pattern in special_patterns:
            matches = re.findall(pattern, user_question)
            for match in matches:
                if 'Model' in pattern:
                    full_name = f"特斯拉Model {match}"
                elif 'ES' in pattern:
                    full_name = f"蔚来ES{match}"
                elif 'ET' in pattern:
                    full_name = f"蔚来ET{match}"
                
                if full_name not in extracted['model_names']:
                    extracted['model_names'].append(full_name)
        
        # 提取地区信息
        for region_name, province_name in self.region_mapping.items():
            if region_name in user_question:
                if province_name.endswith('市'):
                    extracted['cities'].append(region_name + '市')
                else:
                    extracted['provinces'].append(province_name)
        
        # 提取燃料类型
        fuel_keywords = {
            '电动': ['纯电动'],
            '混动': ['插电式混合动力'],
            '汽油': ['汽油'],
            '新能源': ['纯电动', '插电式混合动力']
        }
        
        for keyword, fuel_types in fuel_keywords.items():
            if keyword in user_question:
                extracted['fuel_types'].extend(fuel_types)
        
        # 提取时间范围（改进的时间识别）
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 月份识别（优先级最高）
        month_patterns = [
            r'(\d{4})年(\d{1,2})月',  # 2024年3月
            r'(\d{1,2})月',           # 3月（当年）
        ]
        
        month_found = False
        for pattern in month_patterns:
            matches = re.findall(pattern, user_question)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:  # 年月都有
                    year_int, month_int = int(match[0]), int(match[1])
                else:  # 只有月份
                    year_int, month_int = current_year, int(match)
                
                if 1 <= month_int <= 12:
                    # 计算月份的最后一天
                    if month_int == 12:
                        next_month = 1
                        next_year = year_int + 1
                    else:
                        next_month = month_int + 1
                        next_year = year_int
                    
                    last_day = (datetime(next_year, next_month, 1) - timedelta(days=1)).day
                    
                    extracted['start_date'] = f"{year_int}-{month_int:02d}-01"
                    extracted['end_date'] = f"{year_int}-{month_int:02d}-{last_day}"
                    extracted['time_granularity'] = 'month'
                    month_found = True
                    break
            if month_found:
                break
        
        # 如果没有找到月份，再识别年份
        if not month_found:
            year_patterns = [
                r'(\d{4})年',  # 2024年
                r'(\d{4})',    # 2024
            ]
            
            for pattern in year_patterns:
                years = re.findall(pattern, user_question)
                for year in years:
                    year_int = int(year)
                    if 2020 <= year_int <= current_year + 1:  # 合理的年份范围
                        extracted['start_date'] = f"{year_int}-01-01"
                        extracted['end_date'] = f"{year_int}-12-31"
                        extracted['time_granularity'] = 'year'
                        break
        
        # 季度识别（如果没有找到月份）
        if not month_found:
            quarter_patterns = [
                r'(\d{4})年第([一二三四1234])季度',
                r'第([一二三四1234])季度',
            ]
            
            quarter_map = {'一': 1, '二': 2, '三': 3, '四': 4, '1': 1, '2': 2, '3': 3, '4': 4}
            
            quarter_found = False
            for pattern in quarter_patterns:
                matches = re.findall(pattern, user_question)
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:  # 年份和季度都有
                        year_int = int(match[0])
                        quarter = quarter_map.get(match[1])
                    else:  # 只有季度
                        year_int = current_year
                        quarter = quarter_map.get(match)
                    
                    if quarter:
                        start_month = (quarter - 1) * 3 + 1
                        end_month = quarter * 3
                        
                        # 计算季度最后一天
                        if end_month == 12:
                            last_day = 31
                        else:
                            last_day = (datetime(year_int, end_month + 1, 1) - timedelta(days=1)).day
                        
                        extracted['start_date'] = f"{year_int}-{start_month:02d}-01"
                        extracted['end_date'] = f"{year_int}-{end_month:02d}-{last_day}"
                        extracted['time_granularity'] = 'month'
                        quarter_found = True
                        break
                if quarter_found:
                    break
            
            # 如果找到了季度，更新month_found标志
            if quarter_found:
                month_found = True
        
        # 半年识别
        if '上半年' in user_question:
            year_match = re.search(r'(\d{4})年?上半年', user_question)
            year_int = int(year_match.group(1)) if year_match else current_year
            extracted['start_date'] = f"{year_int}-01-01"
            extracted['end_date'] = f"{year_int}-06-30"
            extracted['time_granularity'] = 'month'
        elif '下半年' in user_question:
            year_match = re.search(r'(\d{4})年?下半年', user_question)
            year_int = int(year_match.group(1)) if year_match else current_year
            extracted['start_date'] = f"{year_int}-07-01"
            extracted['end_date'] = f"{year_int}-12-31"
            extracted['time_granularity'] = 'month'
        
        # 相对时间识别
        if '今年' in user_question:
            extracted['start_date'] = f"{current_year}-01-01"
            extracted['end_date'] = f"{current_year}-12-31"
            extracted['time_granularity'] = 'year'
        elif '去年' in user_question:
            last_year = current_year - 1
            extracted['start_date'] = f"{last_year}-01-01"
            extracted['end_date'] = f"{last_year}-12-31"
            extracted['time_granularity'] = 'year'
        elif '最近一年' in user_question or '近一年' in user_question:
            one_year_ago = datetime.now() - timedelta(days=365)
            extracted['start_date'] = one_year_ago.strftime('%Y-%m-%d')
            extracted['end_date'] = datetime.now().strftime('%Y-%m-%d')
            extracted['time_granularity'] = 'year'
        
        # 时间范围识别（如2023-2024年）
        range_pattern = r'(\d{4})[-到至](\d{4})年?'
        range_match = re.search(range_pattern, user_question)
        if range_match:
            start_year = int(range_match.group(1))
            end_year = int(range_match.group(2))
            extracted['start_date'] = f"{start_year}-01-01"
            extracted['end_date'] = f"{end_year}-12-31"
            extracted['time_granularity'] = 'year'
        
        # 提取数量限制
        limit_patterns = [r'前(\d+)名', r'top\s*(\d+)', r'前(\d+)', r'(\d+)强']
        for pattern in limit_patterns:
            match = re.search(pattern, user_question, re.IGNORECASE)
            if match:
                extracted['limit'] = int(match.group(1))
                break
        
        # 去重
        extracted['brands'] = list(set(extracted['brands']))
        extracted['model_names'] = list(set(extracted['model_names']))
        extracted['provinces'] = list(set(extracted['provinces']))
        extracted['cities'] = list(set(extracted['cities']))
        extracted['fuel_types'] = list(set(extracted['fuel_types']))
        
        return extracted
    
    def _clean_model_names(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """智能处理车型名称，确保与数据库中的实际名称匹配"""
        if not extracted.get('model_names'):
            return extracted
        
        brands = extracted.get('brands', [])
        processed_models = []
        
        # 定义需要保留完整名称的品牌（这些品牌的车型在数据库中包含品牌前缀）
        keep_full_name_brands = ['智己', '蔚来', '理想', '小鹏']
        
        # 定义特斯拉车型的特殊处理（数据库中是大写的MODEL）
        tesla_model_mapping = {
            'Model Y': 'MODEL Y',
            'Model 3': 'MODEL 3', 
            'Model S': 'MODEL S',
            'Model X': 'MODEL X',
            'model y': 'MODEL Y',
            'model 3': 'MODEL 3',
            'model s': 'MODEL S', 
            'model x': 'MODEL X'
        }
        
        for model in extracted['model_names']:
            if not model:
                continue
            
            # 检查是否是需要保留完整名称的品牌
            should_keep_full = False
            for keep_brand in keep_full_name_brands:
                if model.startswith(keep_brand):
                    should_keep_full = True
                    break
            
            # 特斯拉车型的特殊处理
            if model in tesla_model_mapping:
                processed_models.append(tesla_model_mapping[model])
            elif model.startswith('特斯拉') and any(tesla_name in model for tesla_name in tesla_model_mapping.keys()):
                # 处理"特斯拉Model Y"这样的格式
                for original, mapped in tesla_model_mapping.items():
                    if original in model:
                        processed_models.append(mapped)
                        break
                else:
                    processed_models.append(model)
            elif should_keep_full:
                # 对于智己等品牌，保留完整的车型名称
                processed_models.append(model)
            else:
                # 对于其他品牌，尝试去除品牌前缀
                cleaned_model = model
                for brand in brands:
                    if brand and model.startswith(brand) and brand not in keep_full_name_brands:
                        # 去除品牌名称和可能的空格
                        cleaned_model = model[len(brand):].strip()
                        break
                
                # 如果清理后的车型名称不为空，则使用清理后的名称，否则使用原名称
                if cleaned_model:
                    processed_models.append(cleaned_model)
                else:
                    processed_models.append(model)
        
        extracted['model_names'] = processed_models
        return extracted
    
    def _select_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """选择合适的查询模板"""
        user_question = params.get('user_question', '').lower()
        
        # 过滤None值的辅助函数
        def has_valid_values(param_list):
            return param_list and any(item is not None for item in param_list)
        
        # 分析用户问题的关键词来判断意图
        brand_keywords = ['品牌销量', '品牌', '牌子']
        model_keywords = ['车型销量', '车型', '型号', 'model']
        trend_keywords = ['趋势', '变化', '月度', '季度', '走势', '发展']
        region_keywords = ['地区', '省份', '城市', '区域']
        fuel_keywords = ['燃料', '电动', '混动', '汽油', '新能源']
        
        # 根据问题内容和参数选择模板
        # 优先考虑明确的关键词意图
        if any(keyword in user_question for keyword in brand_keywords) and has_valid_values(params.get('brands')):
            # 明确的品牌查询意图
            if any(keyword in user_question for keyword in trend_keywords):
                return self.query_templates['time_trend']
            else:
                return self.query_templates['brand_sales']
        elif any(keyword in user_question for keyword in model_keywords) and has_valid_values(params.get('model_names')):
            # 明确的车型查询意图
            return self.query_templates['model_sales']
        elif any(keyword in user_question for keyword in fuel_keywords) and has_valid_values(params.get('fuel_types')):
            return self.query_templates['fuel_type_analysis']
        elif any(keyword in user_question for keyword in region_keywords) and (has_valid_values(params.get('provinces')) or has_valid_values(params.get('cities'))):
            return self.query_templates['region_sales']
        elif any(keyword in user_question for keyword in trend_keywords) and (params.get('start_date') or params.get('end_date')):
            return self.query_templates['time_trend']
        # 如果没有明确关键词，按参数优先级选择
        elif has_valid_values(params.get('model_names')):
            return self.query_templates['model_sales']
        elif has_valid_values(params.get('fuel_types')):
            return self.query_templates['fuel_type_analysis']
        elif has_valid_values(params.get('provinces')) or has_valid_values(params.get('cities')):
            return self.query_templates['region_sales']
        elif has_valid_values(params.get('brands')):
            # 如果问题包含"趋势"、"变化"、"月度"等关键词，使用时间趋势模板
            if any(keyword in user_question for keyword in trend_keywords):
                return self.query_templates['time_trend']
            # 否则使用品牌销量模板
            else:
                return self.query_templates['brand_sales']
        elif params.get('start_date') or params.get('end_date'):
            return self.query_templates['time_trend']
        else:
            return self.query_templates['general_sales']
    
    def _execute_query(self, data: pd.DataFrame, template_info: Dict[str, Any], params: Dict[str, Any]) -> pd.DataFrame:
        """执行查询（使用pandas模拟SQL）"""
        try:
            # 复制数据以避免修改原始数据
            df = data.copy()
            
            # 应用过滤条件（过滤None值）
            if params.get('brands'):
                valid_brands = [b for b in params['brands'] if b is not None]
                if valid_brands:
                    df = df[df['brand'].isin(valid_brands)]
                    # 重置brand列的分类，避免groupby时包含未使用的分类
                    if hasattr(df['brand'], 'cat'):
                        df['brand'] = df['brand'].cat.remove_unused_categories()
            
            if params.get('provinces'):
                valid_provinces = [p for p in params['provinces'] if p is not None]
                if valid_provinces:
                    df = df[df['province'].isin(valid_provinces)]
            
            if params.get('cities'):
                valid_cities = [c for c in params['cities'] if c is not None]
                if valid_cities:
                    df = df[df['city'].isin(valid_cities)]
            
            if params.get('fuel_types'):
                valid_fuel_types = [f for f in params['fuel_types'] if f is not None]
                if valid_fuel_types:
                    df = df[df['fuel_type'].isin(valid_fuel_types)]
            
            # 时间过滤（转换字符串日期为datetime对象）
            if params.get('start_date'):
                start_date = pd.to_datetime(params['start_date'])
                df = df[df['date'] >= start_date]
            
            if params.get('end_date'):
                end_date = pd.to_datetime(params['end_date'])
                df = df[df['date'] <= end_date]
            
            # 车型过滤
            if params.get('model_names'):
                valid_model_names = [m for m in params['model_names'] if m is not None]
                if valid_model_names:
                    df = df[df['model_name'].isin(valid_model_names)]
            
            # 根据模板类型执行聚合
            template_name = template_info['name']
            
            if '车型销量' in template_name:
                if df.empty:
                    result = pd.DataFrame(columns=['brand', 'model_name', 'total_sales', 'record_count', 'avg_sales'])
                else:
                    result = df.groupby(['brand', 'model_name']).agg({
                        'sales_volume': ['sum', 'count', 'mean']
                    }).round(2)
                    # 修复多级索引列名问题
                    result.columns = result.columns.droplevel(0)  # 移除第一级索引
                    result.columns = ['total_sales', 'record_count', 'avg_sales']
                    result = result.reset_index().sort_values('total_sales', ascending=False)
                    # 过滤掉0销量的记录
                    result = result[result['total_sales'] > 0]
                    
            elif '品牌销量' in template_name:
                if df.empty:
                    base_columns = ['brand', 'total_sales', 'record_count', 'avg_sales']
                    if params.get('model_names'):
                        base_columns.insert(1, 'model_name')
                    result = pd.DataFrame(columns=base_columns)
                else:
                    # 根据是否有车型参数决定分组方式
                    group_cols = ['brand']
                    if params.get('model_names'):
                        group_cols.append('model_name')
                    
                    result = df.groupby(group_cols).agg({
                        'sales_volume': ['sum', 'count', 'mean']
                    }).round(2)
                    # 修复多级索引列名问题
                    result.columns = result.columns.droplevel(0)  # 移除第一级索引
                    result.columns = ['total_sales', 'record_count', 'avg_sales']
                    result = result.reset_index().sort_values('total_sales', ascending=False)
                    # 过滤掉0销量的记录
                    result = result[result['total_sales'] > 0]
                
            elif '时间趋势' in template_name:
                result = df.groupby('date').agg({
                    'sales_volume': 'sum',
                    'brand': 'nunique'
                }).round(2)
                result.columns = ['total_sales', 'brand_count']
                result = result.reset_index().sort_values('date')
                
            elif '地区销量' in template_name:
                # 根据参数决定分组列
                group_cols = ['province', 'city']
                if params.get('brands'):
                    group_cols.append('brand')
                if params.get('model_names'):
                    group_cols.append('model_name')
                    
                result = df.groupby(group_cols).agg({
                    'sales_volume': 'sum',
                    'brand': 'nunique'
                }).round(2)
                # 修复多级索引列名问题
                result.columns = result.columns.droplevel(0)  # 移除第一级索引
                result.columns = ['total_sales', 'brand_count']
                result = result.reset_index().sort_values('total_sales', ascending=False)
                # 过滤掉0销量的记录
                result = result[result['total_sales'] > 0]
                
            elif '燃料类型' in template_name:
                # 根据参数决定分组列
                group_cols = ['fuel_type']
                if params.get('brands'):
                    group_cols.append('brand')
                if params.get('model_names'):
                    group_cols.append('model_name')
                    
                result = df.groupby(group_cols).agg({
                    'sales_volume': ['sum', 'count', 'mean'],
                    'brand': 'nunique'
                }).round(2)
                # 修复多级索引列名问题
                result.columns = result.columns.droplevel(0)  # 移除第一级索引
                result.columns = ['total_sales', 'record_count', 'avg_sales', 'brand_count']
                result = result.reset_index().sort_values('total_sales', ascending=False)
                # 过滤掉0销量的记录
                result = result[result['total_sales'] > 0]
                
            else:  # 综合销量查询
                result = df.groupby('brand')['sales_volume'].sum().reset_index()
                result.columns = ['brand', 'total_sales']
                result = result.sort_values('total_sales', ascending=False)
                # 过滤掉0销量的记录
                result = result[result['total_sales'] > 0].head(10)
            
            # 应用限制
            if params.get('limit'):
                result = result.head(params['limit'])
            
            return result
            
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return pd.DataFrame()
    
    def _format_results(self, result_df: pd.DataFrame, template_info: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """格式化查询结果"""
        try:
            # 转换为字典列表
            data = result_df.to_dict('records') if not result_df.empty else []
            
            # 生成分析统计
            analysis = {
                'query_type': template_info['name'].replace('查询', '').replace('分析', ''),
                'template_used': template_info['name'],
                'total_records': len(data),
                'parameters_used': {k: v for k, v in params.items() if v},
                'data_summary': self._generate_data_summary(result_df)
            }
            
            # 生成可视化配置
            visualization = self._generate_visualization_config(result_df, template_info)
            
            # 生成洞察
            insights = self._generate_insights(result_df, template_info, params)
            
            return {
                'data': data,
                'analysis': analysis,
                'visualization': visualization,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"结果格式化失败: {e}")
            return {
                'data': [],
                'analysis': {'error': str(e)},
                'visualization': {},
                'insights': [f"结果格式化失败: {str(e)}"]
            }
    
    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据摘要"""
        if df.empty:
            return {'message': '无数据'}
        
        summary = {
            'record_count': len(df),
            'columns': list(df.columns)
        }
        
        # 如果有销量列，计算统计信息
        sales_columns = [col for col in df.columns if 'sales' in col.lower()]
        if sales_columns:
            sales_col = sales_columns[0]
            summary['sales_stats'] = {
                'total': float(df[sales_col].sum()),
                'average': float(df[sales_col].mean()),
                'max': float(df[sales_col].max()),
                'min': float(df[sales_col].min())
            }
        
        return summary
    
    def _generate_visualization_config(self, df: pd.DataFrame, template_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成可视化配置"""
        if df.empty:
            return {}
        
        config = {
            'chart_type': 'bar',
            'title': template_info['name'],
            'data_ready': True
        }
        
        # 根据数据类型选择图表类型
        if 'date' in df.columns:
            config['chart_type'] = 'line'
            config['x_axis'] = 'date'
        elif 'brand' in df.columns:
            config['chart_type'] = 'bar'
            config['x_axis'] = 'brand'
        
        # 设置y轴
        sales_columns = [col for col in df.columns if 'sales' in col.lower()]
        if sales_columns:
            config['y_axis'] = sales_columns[0]
        
        return config
    
    def _generate_insights(self, df: pd.DataFrame, template_info: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
        """生成数据洞察 - 使用AI生成深度洞察"""
        if df.empty:
            return ["查询条件下没有找到相关数据"]
        
        try:
            # 尝试使用AI生成深度洞察
            ai_insights = self._generate_ai_insights(df, template_info, params)
            if ai_insights:
                return ai_insights
        except Exception as e:
            logger.warning(f"AI洞察生成失败，使用基础洞察: {e}")
        
        # 备选方案：使用基础洞察
        return self._generate_basic_insights(df, template_info, params)
    
    def _generate_ai_insights(self, df: pd.DataFrame, template_info: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
        """使用AI生成简化洞察"""
        try:
            # 初始化GLM客户端
            glm_client = GLMClient()
            
            # 准备简化数据摘要
            query_data = self._prepare_simple_data_summary(df)
            brands = self._extract_brands(df)
            
            # 调用AI生成洞察
            prompt = AI_INSIGHTS_GENERATION_PROMPT.format(
                query_data=query_data,
                query_params=self._format_query_params(params),
                user_question=params.get('user_question', '销量数据查询')
            )
            
            response = glm_client.generate_response(prompt)
            
            # 简单文本解析
            insights = self._parse_simple_insights(response)
            
            return insights
            
        except Exception as e:
            logger.error(f"AI洞察生成失败: {e}")
            raise
    
    def _generate_basic_insights(self, df: pd.DataFrame, template_info: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
        """生成基础数据洞察（备选方案）"""
        insights = []
        
        # 基本统计洞察
        insights.append(f"查询返回了 {len(df)} 条记录")
        
        # 销量相关洞察
        sales_columns = [col for col in df.columns if 'sales' in col.lower()]
        if sales_columns:
            sales_col = sales_columns[0]
            total_sales = df[sales_col].sum()
            insights.append(f"总销量为 {total_sales:,.0f} 辆")
            
            if len(df) > 1:
                top_item = df.iloc[0]
                if 'brand' in df.columns:
                    insights.append(f"销量最高的品牌是 {top_item['brand']}，销量为 {top_item[sales_col]:,.0f} 辆")
                elif 'province' in df.columns:
                    insights.append(f"销量最高的地区是 {top_item['province']}，销量为 {top_item[sales_col]:,.0f} 辆")
        
        return insights
    
    def _prepare_simple_data_summary(self, df: pd.DataFrame) -> str:
        """为AI准备简化数据摘要"""
        try:
            summary = []
            
            # 检查是否有销量相关列
            sales_col = None
            if 'total_sales' in df.columns:
                sales_col = 'total_sales'
            elif 'sales_volume' in df.columns:
                sales_col = 'sales_volume'
            
            if sales_col:
                # 品牌销量前3（如果有brand列）
                if 'brand' in df.columns:
                    if sales_col == 'total_sales':
                        # 已经聚合的数据
                        top_brands = df.nlargest(3, sales_col)
                        summary.append(f"销量前3品牌：{', '.join([f'{row["brand"]}({row[sales_col]:,.0f}辆)' for _, row in top_brands.iterrows()])}")
                    else:
                        # 原始数据，需要聚合
                        brand_sales = df.groupby('brand')[sales_col].sum().sort_values(ascending=False)
                        top_brands = brand_sales.head(3)
                        summary.append(f"销量前3品牌：{', '.join([f'{b}({v:,.0f}辆)' for b, v in top_brands.items()])}")
                
                # 总销量
                total_sales = df[sales_col].sum()
                summary.append(f"总销量：{total_sales:,.0f}辆")
            else:
                summary.append(f"共{len(df)}条记录")
            
            return "; ".join(summary) if summary else f"共{len(df)}条记录"
            
        except Exception as e:
            logger.error(f"准备简化数据摘要失败: {e}")
            return f"共{len(df)}条记录"
    
    def _extract_brands(self, df: pd.DataFrame) -> str:
        """提取涉及的品牌信息"""
        if 'brand' in df.columns:
            brands = df['brand'].unique().tolist()
            return ', '.join(brands[:5])  # 最多显示5个品牌
        return '未指定品牌'
    
    def _format_query_params(self, params: Dict[str, Any]) -> str:
        """格式化查询参数为可读字符串"""
        try:
            param_parts = []
            
            # 添加品牌信息
            if params.get('brands'):
                # 过滤None值
                brands = [b for b in params['brands'] if b is not None]
                if brands:
                    param_parts.append(f"品牌: {', '.join(brands)}")
            
            # 添加车型信息
            if params.get('model_names'):
                # 过滤None值
                models = [m for m in params['model_names'] if m is not None]
                if models:
                    param_parts.append(f"车型: {', '.join(models)}")
            
            # 添加地区信息
            if params.get('provinces'):
                # 过滤None值
                provinces = [p for p in params['provinces'] if p is not None]
                if provinces:
                    param_parts.append(f"省份: {', '.join(provinces)}")
            if params.get('cities'):
                # 过滤None值
                cities = [c for c in params['cities'] if c is not None]
                if cities:
                    param_parts.append(f"城市: {', '.join(cities)}")
            
            # 添加时间范围
            if params.get('start_date') or params.get('end_date'):
                start_date = params.get('start_date') or ''
                end_date = params.get('end_date') or ''
                time_range = f"{start_date} 至 {end_date}"
                param_parts.append(f"时间范围: {time_range.strip()}")
            
            # 添加燃料类型
            if params.get('fuel_types'):
                # 过滤None值
                fuel_types = [f for f in params['fuel_types'] if f is not None]
                if fuel_types:
                    param_parts.append(f"燃料类型: {', '.join(fuel_types)}")
            
            # 添加限制条件
            if params.get('limit') and params.get('limit') is not None:
                param_parts.append(f"限制条数: {params['limit']}")
            
            return '; '.join(param_parts) if param_parts else '无特定筛选条件'
            
        except Exception as e:
            logger.error(f"格式化查询参数失败: {e}")
            return '参数格式化失败'
    
    def _parse_simple_insights(self, response: str) -> List[str]:
        """简单解析AI响应为洞察列表"""
        try:
            # 按行分割并清理
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            # 过滤掉太短的行
            insights = [line for line in lines if len(line) > 10]
            
            # 如果没有有效洞察，返回原始响应的前200字符
            if not insights:
                insights = [response[:200] + '...' if len(response) > 200 else response]
            
            return insights[:5]  # 最多返回5个洞察
            
        except Exception as e:
            logger.error(f"洞察解析失败: {e}")
            return ["AI分析完成，请查看具体数据结果"]
    

    
    def _generate_brand_sales_summary(self, data: List[Dict], analysis: Dict[str, Any]) -> str:
        """生成品牌销量摘要"""
        if not data:
            return "未找到相关品牌的销量数据。"
        
        total_sales = sum(item.get('total_sales', 0) for item in data)
        top_brand = data[0]
        
        summary = f"查询到 {len(data)} 个品牌的销量数据，总销量为 {total_sales:,.0f} 辆。"
        summary += f"销量最高的品牌是 {top_brand['brand']}，销量为 {top_brand['total_sales']:,.0f} 辆。"
        
        return summary
    
    def _generate_time_trend_summary(self, data: List[Dict], analysis: Dict[str, Any]) -> str:
        """生成时间趋势摘要"""
        if not data:
            return "未找到相关时间段的销量数据。"
        
        total_sales = sum(item.get('total_sales', 0) for item in data)
        date_range = f"{data[0]['date']} 到 {data[-1]['date']}"
        
        summary = f"时间段 {date_range} 内，总销量为 {total_sales:,.0f} 辆，"
        summary += f"涵盖 {len(data)} 个时间点。"
        
        return summary
    
    def _generate_region_sales_summary(self, data: List[Dict], analysis: Dict[str, Any]) -> str:
        """生成地区销量摘要"""
        if not data:
            return "未找到相关地区的销量数据。"
        
        total_sales = sum(item.get('total_sales', 0) for item in data)
        top_region = data[0]
        
        summary = f"查询到 {len(data)} 个地区的销量数据，总销量为 {total_sales:,.0f} 辆。"
        summary += f"销量最高的地区是 {top_region['province']} {top_region['city']}，销量为 {top_region['total_sales']:,.0f} 辆。"
        
        return summary
    
    def _generate_fuel_type_summary(self, data: List[Dict], analysis: Dict[str, Any]) -> str:
        """生成燃料类型摘要"""
        if not data:
            return "未找到相关燃料类型的销量数据。"
        
        total_sales = sum(item.get('total_sales', 0) for item in data)
        top_fuel = data[0]
        
        summary = f"查询到 {len(data)} 种燃料类型的销量数据，总销量为 {total_sales:,.0f} 辆。"
        summary += f"销量最高的燃料类型是 {top_fuel['fuel_type']}，销量为 {top_fuel['total_sales']:,.0f} 辆。"
        
        return summary
    
    def _generate_general_summary(self, data: List[Dict], analysis: Dict[str, Any]) -> str:
        """生成通用摘要"""
        if not data:
            return "查询未返回任何数据。"
        
        return f"查询完成，返回 {len(data)} 条记录。"


# 为了支持Jinja2模板中的tojsonfilter
def tojsonfilter(value):
    """将值转换为JSON格式的字符串"""
    import json
    return json.dumps(value)


# 注册自定义过滤器
from jinja2 import Environment
env = Environment()
env.filters['tojsonfilter'] = tojsonfilter