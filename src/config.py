"""
配置管理模块
负责管理所有配置信息，包括API端点、模型配置、缓存配置等
"""

import logging
from Bio import Entrez
from typing import Dict, List, Any

# ================= PubMed配置 =================
# 请替换为您自己的邮箱，这是PubMed API的要求，用于追踪高频访问
Entrez.email = "varian69@gmail.com" 

# 检索关键词 (以MCT为例，复用之前的逻辑)
SEARCH_TERM = """
("Medium-chain triglycerides" OR "MCT" OR "Caprylic acid") AND ("Weight loss" OR "Body composition" OR "Fat mass") AND ("Adults"[Mesh] OR "Adult") AND ("Obesity"[Mesh] OR "Overweight"[Mesh] OR "Obesity" OR "Overweight") NOT ("Diabetes Mellitus"[Mesh] OR "Diabetes" OR "Hypertension"[Mesh] OR "High blood pressure" OR "Cardiovascular Diseases"[Mesh] OR "Metabolic Syndrome"[Mesh] OR "Neoplasms"[Mesh] OR "Cancer" OR "Pregnancy" OR "Pregnant" OR "Child" OR "Adolescent")
"""

# 想要获取的文献数量
MAX_RESULTS = 100 

# ================= AI API配置 =================
# 多种API端点尝试
API_ENDPOINTS = [
    "https://api.gptgod.online/v1/chat/completions",
    "https://api.minimax.chat/v1/text/chatcompletion_v2",
    "https://api.deepseek.com/v1/chat/completions"
]

# API密钥池配置 - 多个密钥用于提高请求成功率
API_KEYS_POOL = [
    "sk-1wLZqqkXDT9shZzgTqNRc0wNB6K4Kmu1t0kov0KA5I3auqVf",  # 主密钥
    "sk-19GhS2EHMvZJZrm4LYdL94KrAfIb5ckAhwH7Btcorg23zh8H",  # 备用密钥1
    "sk-t0WZJnqINXX2LnRvPIvRvhMLIcfYtZ76UvOjHf82IGPcYRj1",  # 备用密钥2
]

# 向后兼容 - 保留原有单密钥配置
API_KEY = API_KEYS_POOL[0]

# API密钥池管理配置
API_KEY_POOL_CONFIG = {
    "max_failure_count": 3,        # 最大失败次数，超过后暂时禁用密钥
    "disable_duration": 300,       # 密钥禁用时长（秒），5分钟
    "success_reset_threshold": 2,  # 成功次数阈值，重置失败计数
    "enable_key_rotation": True,   # 启用密钥轮换
    "log_key_usage": True          # 是否记录密钥使用情况（不记录具体密钥内容）
}

# 模型配置
MODEL_CONFIGS = [
    ("gpt-5-mini", API_ENDPOINTS[0]),  # GPTGod + gpt-5-mini (默认模型)
    ("gpt-3.5-turbo", API_ENDPOINTS[0]),  # GPTGod + gpt-3.5
    ("gpt-4", API_ENDPOINTS[0]),  # GPTGod + gpt-4
]

# ================= 缓存配置 =================
# 国家识别缓存配置
COUNTRY_CACHE = {}  # 简单内存缓存
COUNTRY_CACHE_MAX_SIZE = 1000
COUNTRY_CACHE_TTL = 3600  # 1小时过期

# ================= 功能配置 =================
ENABLE_WEB_SEARCH = True  # 是否启用web search功能
ENABLE_FULLTEXT_EXTRACTION = False  # 是否启用全文提取功能
REQUEST_DELAY = 2.0  # API请求间隔（秒），避免429错误

# ================= 日志配置 =================
def setup_logging():
    """设置日志配置"""
    # 配置日志 - 启用调试模式
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')
    logger = logging.getLogger(__name__)

    # 设置特定模块的日志级别
    logging.getLogger('pubmed').setLevel(logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.WARNING)  # 减少第三方库的日志噪音
    
    return logger

# 默认配置字典
DEFAULT_CONFIG = {
    "search_term": SEARCH_TERM,
    "max_results": MAX_RESULTS,
    "api_endpoints": API_ENDPOINTS,
    "api_keys_pool": API_KEYS_POOL,
    "api_key_pool_config": API_KEY_POOL_CONFIG,
    "model_configs": MODEL_CONFIGS,
    "country_cache": COUNTRY_CACHE,
    "country_cache_max_size": COUNTRY_CACHE_MAX_SIZE,
    "country_cache_ttl": COUNTRY_CACHE_TTL,
    "enable_web_search": ENABLE_WEB_SEARCH,
    "enable_fulltext_extraction": ENABLE_FULLTEXT_EXTRACTION,
    "request_delay": REQUEST_DELAY
}

# ================= 配置管理类 =================
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """初始化配置管理器"""
        self.config = config_dict or DEFAULT_CONFIG
        self.logger = setup_logging()
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
        self.logger.debug(f"配置已更新: {key} = {value}")
    
    def update(self, config_dict: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(config_dict)
        self.logger.debug(f"配置已批量更新: {len(config_dict)} 项")
    
    def get_search_term(self) -> str:
        """获取搜索关键词"""
        return self.get("search_term")
    
    def get_max_results(self) -> int:
        """获取最大结果数"""
        return self.get("max_results", 100)
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API相关配置"""
        return {
            "endpoints": self.get("api_endpoints"),
            "keys_pool": self.get("api_keys_pool"),
            "pool_config": self.get("api_key_pool_config"),
            "model_configs": self.get("model_configs"),
            "request_delay": self.get("request_delay")
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存相关配置"""
        return {
            "country_cache": self.get("country_cache"),
            "country_cache_max_size": self.get("country_cache_max_size"),
            "country_cache_ttl": self.get("country_cache_ttl")
        }
    
    def get_feature_config(self) -> Dict[str, Any]:
        """获取功能开关配置"""
        return {
            "enable_web_search": self.get("enable_web_search"),
            "enable_fulltext_extraction": self.get("enable_fulltext_extraction")
        }

# 全局配置管理器实例
config_manager = ConfigManager()