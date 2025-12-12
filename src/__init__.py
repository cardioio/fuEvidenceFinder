"""
PubMed文献分析工具包 - 重构后的模块化版本

这个包提供了PubMed文献搜索、信息提取和分析的完整功能。
"""

# 导入主要模块
from src.config import ConfigManager
from src.api_key_manager import APIKeyPoolManager, api_key_pool
from src.pubmed_scraper import PubMedScraper, search_pubmed, fetch_details
from src.data_parser import DataParser, extract_info_with_regex, parse_record
from src.ai_extractor import AIExtractor, extract_info_with_ai
from src.fulltext_extractor import (
    FullTextExtractor, 
    check_full_text_availability, 
    extract_full_text_content,
    analyze_pmid_with_full_text
)
from src.tests import TestFunctions, test_ai_extraction, test_api_key_pool, test_country_processing, run_comprehensive_test

# 导入主程序
from src.main import MainApplication, main

# 版本信息
__version__ = "2.0.0"
__author__ = "PubMed Analysis Tool"
__description__ = "PubMed文献分析工具 - 重构版"

# 导出的公共接口
__all__ = [
    # 配置管理
    'ConfigManager',
    
    # API密钥管理
    'APIKeyPoolManager',
    'api_key_pool',
    
    # PubMed搜索
    'PubMedScraper',
    'search_pubmed',
    'fetch_details',
    
    # 数据解析
    'DataParser',
    'extract_info_with_regex',
    'parse_record',
    
    # AI信息提取
    'AIExtractor',
    'extract_info_with_ai',
    
    # 全文提取
    'FullTextExtractor',
    'check_full_text_availability',
    'extract_full_text_content',
    'analyze_pmid_with_full_text',
    
    # 测试功能
    'TestFunctions',
    'test_ai_extraction',
    'test_api_key_pool',
    'test_country_processing',
    'run_comprehensive_test',
    
    # 主程序
    'MainApplication',
    'main',
    
    # 版本信息
    '__version__',
    '__author__',
    '__description__'
]

# 模块级便利函数
def create_scraper(**kwargs):
    """创建PubMed搜索器实例的便利函数"""
    return PubMedScraper(**kwargs)

def create_extractor(**kwargs):
    """创建AI信息提取器实例的便利函数"""
    return AIExtractor(**kwargs)

def create_parser(**kwargs):
    """创建数据解析器实例的便利函数"""
    return DataParser(**kwargs)

# 向后兼容性别名
PubMedTool = PubMedScraper
Extractor = AIExtractor
Parser = DataParser