import pandas as pd
import re
from Bio import Entrez
from datetime import datetime
import requests
import json
import time
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup

# ================= 配置区域 =================
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

# 国家识别缓存配置
COUNTRY_CACHE = {}  # 简单内存缓存
COUNTRY_CACHE_MAX_SIZE = 1000
COUNTRY_CACHE_TTL = 3600  # 1小时过期

ENABLE_WEB_SEARCH = True  # 是否启用web search功能
REQUEST_DELAY = 2.0  # API请求间隔（秒），避免429错误

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================= API密钥池管理器 =================
class APIKeyPoolManager:
    """
    API密钥池管理器 - 提供密钥的动态管理、自动轮换和状态监控功能
    """
    
    def __init__(self, api_keys: list, config: dict):
        """
        初始化API密钥池管理器
        
        Args:
            api_keys: API密钥列表
            config: 配置字典
        """
        self.api_keys = api_keys
        self.config = config
        self.current_key_index = 0
        self.key_states = {}
        
        # 初始化每个密钥的状态
        for i, key in enumerate(api_keys):
            key_id = f"key_{i+1}"  # 使用key_1, key_2等作为密钥标识符
            self.key_states[key_id] = {
                "key": key,
                "failure_count": 0,
                "success_count": 0,
                "is_disabled": False,
                "disabled_until": None,
                "last_used": None,
                "total_requests": 0,
                "total_successes": 0
            }
    
    def get_available_key(self) -> Optional[str]:
        """
        获取下一个可用的API密钥
        
        Returns:
            可用的API密钥，如果所有密钥都不可用则返回None
        """
        if not self.config.get("enable_key_rotation", True):
            return self.api_keys[0] if self.api_keys else None
            
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            key_id = f"key_{self.current_key_index + 1}"
            state = self.key_states[key_id]
            
            # 检查密钥是否被禁用
            if self._is_key_disabled(state):
                # 尝试下一个密钥
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                attempts += 1
                continue
                
            # 密钥可用
            return state["key"]
        
        # 所有密钥都不可用
        logger.error("所有API密钥都不可用")
        return None
    
    def _is_key_disabled(self, key_state: dict) -> bool:
        """
        检查密钥是否被禁用
        
        Args:
            key_state: 密钥状态字典
            
        Returns:
            布尔值，表示密钥是否被禁用
        """
        if not key_state["is_disabled"]:
            return False
            
        # 检查禁用时间是否已过
        if key_state["disabled_until"] and time.time() > key_state["disabled_until"]:
            # 重新启用密钥
            key_state["is_disabled"] = False
            key_state["disabled_until"] = None
            logger.info(f"密钥重新启用")
            return False
            
        return True
    
    def report_success(self, key: str):
        """
        报告API请求成功
        
        Args:
            key: 使用的API密钥
        """
        key_id = self._get_key_id(key)
        if key_id and key_id in self.key_states:
            state = self.key_states[key_id]
            state["success_count"] += 1
            state["total_successes"] += 1
            state["last_used"] = time.time()
            
            # 如果有失败记录，重置失败计数
            if state["failure_count"] > 0:
                state["failure_count"] = max(0, state["failure_count"] - 1)
            
            # 记录密钥使用情况
            if self.config.get("log_key_usage", True):
                logger.debug(f"密钥 {key_id} 请求成功，累计成功: {state['total_successes']}")
    
    def report_failure(self, key: str, error_type: str = "unknown"):
        """
        报告API请求失败
        
        Args:
            key: 使用的API密钥
            error_type: 错误类型
        """
        key_id = self._get_key_id(key)
        if key_id and key_id in self.key_states:
            state = self.key_states[key_id]
            state["failure_count"] += 1
            state["total_requests"] += 1
            state["last_used"] = time.time()
            
            # 检查是否需要禁用密钥
            max_failures = self.config.get("max_failure_count", 3)
            if state["failure_count"] >= max_failures:
                self._disable_key(key_id, error_type)
            
            # 记录密钥使用情况
            if self.config.get("log_key_usage", True):
                logger.warning(f"密钥 {key_id} 请求失败 ({error_type})，失败次数: {state['failure_count']}")
    
    def _disable_key(self, key_id: str, reason: str):
        """
        禁用密钥
        
        Args:
            key_id: 密钥标识符
            reason: 禁用原因
        """
        disable_duration = self.config.get("disable_duration", 300)
        state = self.key_states[key_id]
        
        state["is_disabled"] = True
        state["disabled_until"] = time.time() + disable_duration
        
        logger.warning(f"密钥 {key_id} 因失败次数过多被临时禁用，原因: {reason}，禁用时长: {disable_duration}秒")
    
    def _get_key_id(self, key: str) -> Optional[str]:
        """
        根据密钥获取密钥标识符
        
        Args:
            key: API密钥
            
        Returns:
            密钥标识符，如果找不到返回None
        """
        for key_id, state in self.key_states.items():
            if state["key"] == key:
                return key_id
        return None
    
    def get_key_statistics(self) -> dict:
        """
        获取所有密钥的统计信息
        
        Returns:
            包含统计信息的字典
        """
        stats = {}
        for key_id, state in self.key_states.items():
            stats[key_id] = {
                "is_disabled": state["is_disabled"],
                "failure_count": state["failure_count"],
                "success_count": state["success_count"],
                "total_requests": state["total_requests"],
                "total_successes": state["total_successes"],
                "success_rate": state["total_successes"] / max(1, state["total_requests"]),
                "last_used": state["last_used"]
            }
        return stats
    
    def rotate_key(self):
        """
        轮换到下一个密钥
        """
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.debug(f"密钥轮换到索引: {self.current_key_index}")

# 创建全局API密钥池管理器实例
api_key_pool = APIKeyPoolManager(API_KEYS_POOL, API_KEY_POOL_CONFIG)

# ================= 主程序配置 =================
# 全局配置
ENABLE_FULLTEXT_EXTRACTION = False  # 是否启用全文提取功能
# ===========================================

def search_pubmed(query, max_results=20):
    """在PubMed中搜索并返回ID列表"""
    print(f"正在搜索: {query.strip()}...")
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        return record["IdList"]
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def fetch_details(id_list):
    """根据ID获取文献详细信息"""
    print(f"正在获取 {len(id_list)} 篇文献的详细信息...")
    ids = ",".join(id_list)
    try:
        handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        return records['PubmedArticle']
    except Exception as e:
        print(f"获取详情失败: {e}")
        return []

def extract_sample_size(abstract_text):
    """
    尝试使用正则表达式从摘要中提取样本量 (n=xxx)
    这只是一个简单的启发式算法，不一定100%准确
    """
    if not abstract_text:
        return "N/A"
    
    # 匹配常见的样本量表达，如 n=100, 100 participants, 100 subjects
    patterns = [
        r"n\s*=\s*(\d+)",
        r"(\d+)\s*participants",
        r"(\d+)\s*subjects",
        r"(\d+)\s*patients"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, abstract_text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "需人工确认"

def parse_record(article):
    """解析单篇文献，映射到目标表格列"""
    data = {}
    medline = article['MedlineCitation']
    article_data = medline['Article']
    
    # 1. 发表年份
    try:
        pub_date = article_data['Journal']['JournalIssue']['PubDate']
        year = pub_date.get('Year', '')
        if not year and 'MedlineDate' in pub_date:
            year = pub_date['MedlineDate'].split(' ')[0]
        data['发表年份'] = year
    except:
        data['发表年份'] = "N/A"

    # 2. 数据收集年份 (通过AI提取) - 稍后从AI提取结果获取，先设为默认值
    data['数据收集年份'] = "需AI提取"

    # 3. 国家 (尝试从作者机构提取，通常取第一作者)
    data['国家'] = extract_country_from_affiliation(article_data)

    # 4. 研究类型 (从PublicationTypeList提取)
    try:
        pt_list = [pt.title() for pt in article_data.get('PublicationTypeList', [])]
        if "Meta-Analysis" in pt_list:
            r_type = "Meta-Analysis"
        elif "Randomized Controlled Trial" in pt_list:
            r_type = "RCT"
        elif "Review" in pt_list:
            r_type = "Review"
        else:
            r_type = ", ".join(pt_list)
        data['研究类型'] = r_type
    except:
        data['研究类型'] = "N/A"

    # 5. 研究对象 & 6. 样本量
    abstract_text = ""
    if 'Abstract' in article_data and 'AbstractText' in article_data['Abstract']:
        # AbstractText 有时是列表（分段摘要），有时是字符串
        abs_content = article_data['Abstract']['AbstractText']
        if isinstance(abs_content, list):
            abstract_text = " ".join([str(item) for item in abs_content])
        else:
            abstract_text = str(abs_content)
    
    # 使用AI统一提取信息（不再依赖正则表达式）
    logger.info("开始使用AI提取研究信息...")
    
    # 直接使用AI提取所有信息
    print("  📤 正在将摘要/原文html发给AI询问中...")
    ai_extracted = extract_info_with_ai(abstract_text)
    print("  📥 AI数据已返回")
    logger.info(f"AI提取结果：{ai_extracted}")
    
    # 更新数据字段
    data['研究对象'] = ai_extracted.get('研究对象', "需人工确认")
    data['样本量'] = ai_extracted.get('样本量', "需人工确认")
    data['推荐补充剂量/用法'] = ai_extracted.get('推荐补充剂量/用法', "需人工确认")
    data['作用机理'] = ai_extracted.get('作用机理', "需人工确认")
    data['摘要主要内容'] = ai_extracted.get('摘要主要内容', "需人工确认")
    data['结论摘要'] = ai_extracted.get('结论摘要', "需人工确认")  # 从AI提取结果中获取中文结论摘要
    data['数据收集年份'] = ai_extracted.get('数据收集年份', "需人工确认")  # 从AI提取结果中获取数据收集年份
    
    # 9. 证据等级 (基于研究类型预判)
    if "Meta-Analysis" in data['研究类型']:
        data['证据等级'] = "Level 1"
    elif "RCT" in data['研究类型']:
        data['证据等级'] = "Level 2"
    else:
        data['证据等级'] = "待定"

    # 额外信息方便核对
    data['标题'] = article_data.get('ArticleTitle', '')
    data['PMID'] = medline.get('PMID', '')

    # 如果启用全文提取功能，获取PMID并进行全文分析
    if ENABLE_FULLTEXT_EXTRACTION and data['PMID']:
        try:
            print(f"  🔍 正在检查PMID {data['PMID']} 的全文可用性...")
            
            # 使用全文分析功能
            fulltext_analysis = analyze_pmid_with_full_text(data['PMID'])
            
            # 将全文分析结果添加到数据中
            data['免费全文状态'] = fulltext_analysis.get('is_free', False)
            data['免费全文链接数'] = len(fulltext_analysis.get('links', []))
            data['全文提取状态'] = fulltext_analysis.get('extraction_success', False)
            data['全文内容摘要'] = fulltext_analysis.get('extracted_content', {}).get('abstract', '未提取')
            
            if fulltext_analysis.get('is_free'):
                print(f"  ✅ 发现免费全文: {data['免费全文链接数']} 个链接")
            else:
                print(f"  ❌ 无免费全文")
                
        except Exception as e:
            logger.error(f"处理PMID {data['PMID']} 全文分析时出错: {e}")
            data['免费全文状态'] = False
            data['免费全文链接数'] = 0
            data['全文提取状态'] = False
            data['全文内容摘要'] = "分析失败"

    return data

def extract_country_from_affiliation(article_data: Dict) -> str:
    """
    从作者机构信息中提取国家名称 - 基于GPT AI的简化实现
    
    Args:
        article_data: 从PubMed获取的文章数据
        
    Returns:
        国家名称字符串
    """
    try:
        # 尝试从第一作者提取机构信息
        if 'AuthorList' not in article_data or not article_data['AuthorList']:
            logger.warning("没有找到作者信息，返回需人工确认")
            return "需人工确认"
            
        first_author = article_data['AuthorList'][0]
        
        # 获取机构信息
        affiliation = ""
        if 'AffiliationInfo' in first_author and first_author['AffiliationInfo']:
            affiliation = first_author['AffiliationInfo'][0].get('Affiliation', '')
        elif 'Affiliation' in first_author:
            affiliation = first_author['Affiliation']
        
        if not affiliation:
            logger.warning("没有找到机构信息，返回需人工确认")
            return "需人工确认"
        
        # 清理机构信息用于缓存键
        clean_affiliation = affiliation.replace('\n', ' ').replace('\r', ' ').strip()
        
        # 检查缓存
        cache_key = f"{hash(clean_affiliation)}_{len(clean_affiliation)}"
        if cache_key in COUNTRY_CACHE:
            cached_result, cache_time = COUNTRY_CACHE[cache_key]
            if time.time() - cache_time < COUNTRY_CACHE_TTL:
                logger.debug(f"从缓存获取国家信息: {cached_result}")
                return cached_result
        
        # 使用AI进行国家识别
        ai_result = _extract_country_with_ai(clean_affiliation)
        
        if ai_result and ai_result != "需人工确认":
            # 更新缓存
            _update_country_cache(cache_key, ai_result)
            return ai_result
        
        # 回退到简单的关键词匹配
        logger.info("AI识别失败，使用回退机制")
        return _fallback_country_extraction(clean_affiliation)
        
    except Exception as e:
        logger.error(f"提取国家信息时出错: {e}")
        return "需人工确认"

def _extract_country_with_ai(affiliation: str) -> str:
    """
    使用GPT AI从机构信息中提取国家名称
    
    Args:
        affiliation: 机构信息字符串
        
    Returns:
        国家名称字符串
    """
    prompt = f"""请从以下作者机构信息中提取国家名称。请只返回国家名称，如果无法确定则返回"需人工确认"。

机构信息：
{affiliation}

要求：
1. 只返回国家名称，如"United States"、"China"、"Germany"等
2. 如果信息不足或无法确定，返回"需人工确认"
3. 不要包含其他文字或解释
4. 统一使用标准国家名称（如"United States"而非"USA"）
"""

    try:
        # 使用简化的AI调用函数
        result = _call_ai_api(prompt, "country_extraction")
        if result:
            result = result.strip()
            # 验证返回结果
            if result and result != "需人工确认":
                logger.info(f"AI识别国家成功: {result}")
                return result
        return "需人工确认"
    except Exception as e:
        logger.error(f"AI国家识别失败: {e}")
        return "需人工确认"

def _fallback_country_extraction(affiliation: str) -> str:
    """
    回退机制：简单的关键词匹配提取国家
    
    Args:
        affiliation: 机构信息字符串
        
    Returns:
        国家名称字符串
    """
    # 简化的国家关键词映射
    country_keywords = {
        "United States": ["USA", "US", "America", "United States", "American"],
        "China": ["China", "Chinese", "Beijing", "Shanghai", "Guangzhou"],
        "United Kingdom": ["UK", "Britain", "England", "Scotland", "Wales"],
        "Germany": ["Germany", "German", "Deutschland"],
        "Japan": ["Japan", "Japanese", "Tokyo", "Osaka"],
        "Australia": ["Australia", "Australian", "Sydney", "Melbourne"],
        "Canada": ["Canada", "Canadian"],
        "France": ["France", "French"],
        "Italy": ["Italy", "Italian"],
        "Spain": ["Spain", "Spanish"],
        "Netherlands": ["Netherlands", "Dutch"],
        "South Korea": ["Korea", "Korean", "Seoul"],
        "India": ["India", "Indian", "Mumbai", "Delhi"],
        "Singapore": ["Singapore", "Singaporean"],
        "Taiwan": ["Taiwan", "Taiwanese"],
        "Hong Kong": ["Hong Kong"],
        "Brazil": ["Brazil", "Brazilian"],
        "Mexico": ["Mexico", "Mexican"]
    }
    
    affiliation_upper = affiliation.upper()
    
    for country, keywords in country_keywords.items():
        for keyword in keywords:
            if keyword.upper() in affiliation_upper:
                logger.info(f"回退机制识别国家: {country} (匹配关键词: {keyword})")
                return country
    
    logger.info("回退机制也未能识别国家，返回需人工确认")
    return "需人工确认"

def _call_ai_api(prompt: str, context: str) -> str:
    """
    调用AI API的简化接口
    
    Args:
        prompt: 提示词
        context: 上下文标识
        
    Returns:
        AI返回的文本
    """
    try:
        # 定义模型配置
        model_configs = [
            ("gpt-3.5-turbo", API_ENDPOINTS[0]),  # GPTGod + gpt-3.5
            ("gpt-4", API_ENDPOINTS[0]),  # GPTGod + gpt-4
            ("deepseek-chat", API_ENDPOINTS[2])  # DeepSeek + deepseek-chat
        ]
        
        # 使用现有的extract_info_with_ai逻辑，但只获取简单文本结果
        max_retries_per_config = 2
        max_total_retries = 6
        
        total_attempts = 0
        for model, endpoint in model_configs:
            if total_attempts >= max_total_retries:
                break
                
            for retry in range(max_retries_per_config):
                total_attempts += 1
                if total_attempts >= max_total_retries:
                    break
                    
                # 获取可用密钥
                api_key = api_key_pool.get_available_key()
                if not api_key:
                    logger.error("没有可用的API密钥")
                    return ""
                
                try:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                    
                    payload = {
                        'model': model,
                        'messages': [
                            {
                                'role': 'user',
                                'content': prompt
                            }
                        ],
                        'max_tokens': 100,
                        'temperature': 0.1
                    }
                    
                    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0]['message']['content'].strip()
                            api_key_pool.report_success(api_key)
                            logger.debug(f"AI API调用成功 ({context})")
                            return content
                        else:
                            api_key_pool.report_failure(api_key, "invalid_response")
                    elif response.status_code == 429:
                        # 限流错误，使用指数退避
                        wait_time = (2 ** retry) + random.uniform(0, 1)
                        logger.warning(f"API限流，等待 {wait_time:.1f} 秒")
                        time.sleep(wait_time)
                        api_key_pool.report_failure(api_key, "rate_limit")
                        continue
                    elif response.status_code in [401, 403]:
                        # 认证错误，切换密钥
                        logger.warning(f"API密钥认证失败，尝试下一个密钥")
                        api_key_pool.report_failure(api_key, "auth_error")
                        break
                    else:
                        logger.error(f"API调用失败: {response.status_code} - {response.text}")
                        api_key_pool.report_failure(api_key, f"http_{response.status_code}")
                        
                except requests.exceptions.Timeout:
                    logger.error(f"API调用超时")
                    api_key_pool.report_failure(api_key, "timeout")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.error(f"API请求异常: {e}")
                    api_key_pool.report_failure(api_key, "request_error")
                    continue
                except Exception as e:
                    logger.error(f"处理API响应时出错: {e}")
                    api_key_pool.report_failure(api_key, "processing_error")
                    continue
        
        logger.error("所有AI API调用尝试均失败")
        return ""
        
    except Exception as e:
        logger.error(f"调用AI API时出错: {e}")
        return ""

def _update_country_cache(key: str, country: str):
    """
    更新国家识别缓存
    
    Args:
        key: 缓存键
        country: 国家名称
    """
    try:
        # 检查缓存大小限制
        if len(COUNTRY_CACHE) >= COUNTRY_CACHE_MAX_SIZE:
            # 删除最旧的条目（简单实现：删除第一个）
            oldest_key = next(iter(COUNTRY_CACHE))
            del COUNTRY_CACHE[oldest_key]
            logger.debug("缓存已满，删除最旧条目")
        
        COUNTRY_CACHE[key] = (country, time.time())
        logger.debug(f"更新国家缓存: {key[:20]}... -> {country}")
    except Exception as e:
        logger.error(f"更新缓存时出错: {e}")



def extract_info_with_regex(abstract_text: str) -> Dict[str, str]:
    """
    使用正则表达式从摘要中提取结构化信息（主要方法）
    """
    result = {
        "研究对象": "未明确说明",
        "样本量": "未明确说明", 
        "推荐补充剂量/用法": "未明确说明",
        "作用机理": "未明确说明"
    }
    
    if not abstract_text:
        return result
    
    # 提取样本量
    sample_patterns = [
        r"(\d+)\s*participants?",
        r"(\d+)\s*subjects?",
        r"(\d+)\s*patients?",
        r"n\s*=\s*(\d+)",
        r"sample\s+size\s+(?:of\s+)?(\d+)",
        r"involving\s+(\d+)\s+(?:participants|subjects|patients)",
        r"(\d+)\s+(?:healthy\s+)?volunteers?"
    ]
    
    for pattern in sample_patterns:
        match = re.search(pattern, abstract_text, re.IGNORECASE)
        if match:
            result["样本量"] = match.group(1)
            break
    
    # 提取研究对象特征
    subject_patterns = [
        r"(\d+)-?(\d+)?\s*years?\s+old",
        r"aged\s+(\d+)-?(\d+)?\s*years?",
        r"(overweight|obese|healthy)\s+(?:adults?|participants?)",
        r"(men|women|male|female)",
        r"(diabetes|hypertension|metabolic\s+syndrome)",
        r"(BMI\s+\d+-\d+)"
    ]
    
    subjects = []
    for pattern in subject_patterns:
        matches = re.findall(pattern, abstract_text, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                subjects.extend([m for m in matches[0] if m])
            else:
                subjects.extend(matches)
    
    if subjects:
        result["研究对象"] = "、".join(subjects)
    
    # 提取剂量信息
    dose_patterns = [
        r"(\d+)\s*ml\s+(?:MCT\s+)?oil\s+daily",
        r"(\d+)\s*g\s+(?:MCT\s+)?daily", 
        r"(\d+)\s*ml\s+per\s+day",
        r"(\d+)\s*g\s+per\s+day",
        r"(\d+)\s*ml\s+twice\s+daily",
        r"(\d+)\s*g\s+(\d+)\s*times\s+per\s+day"
    ]
    
    for pattern in dose_patterns:
        match = re.search(pattern, abstract_text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                result["推荐补充剂量/用法"] = f"{match.group(1)}g {match.group(2)}次/天"
            else:
                result["推荐补充剂量/用法"] = match.group(0)
            break
    
    # 提取作用机理
    mechanism_patterns = [
        r"(increase\s+thermogenesis)",
        r"(promote\s+fat\s+oxidation)",
        r"(enhance\s+ketone\s+production)",
        r"(increase\s+energy\s+expenditure)",
        r"(enhance\s+satiety)",
        r"(promote\s+ketogenesis)",
        r"(stimulate\s+uncoupling\s+proteins)",
        r"(rapid\s+oxidation)"
    ]
    
    mechanisms = []
    for pattern in mechanism_patterns:
        matches = re.findall(pattern, abstract_text, re.IGNORECASE)
        if matches:
            mechanisms.extend(matches)
    
    if mechanisms:
        result["作用机理"] = "；".join(mechanisms)
    
    return result

def extract_info_with_ai(abstract_text: str) -> Dict[str, str]:
    """
    使用GPT-4.1 API从摘要中提取结构化信息（主要方法）
    
    Args:
        abstract_text: 文献摘要文本
        
    Returns:
        包含提取信息的字典，包含以下字段：
        - 研究对象
        - 样本量  
        - 推荐补充剂量/用法
        - 作用机理
        - 摘要主要内容
        - 数据收集年份
    """
    if not abstract_text or abstract_text.strip() == "":
        logger.warning("摘要文本为空，返回默认空值")
        return {
            "研究对象": "需人工确认",
            "样本量": "需人工确认", 
            "推荐补充剂量/用法": "需人工确认",
            "作用机理": "需人工确认",
            "摘要主要内容": "需人工确认",
            "结论摘要": "需人工确认",
            "国家": "需人工确认",
            "数据收集年份": "需人工确认"
        }
    
    # 构建全中文提示词，要求AI从摘要中提取特定信息
    prompt = f"""
请分析以下英文学术文献摘要，并提取以下八个方面的中文信息：

**摘要原文：**
{abstract_text}

**请提取以下信息（如果摘要中没有相关信息，请标注"未明确说明"）：**

1. **研究对象**：研究涉及的人群特征（年龄范围、性别、健康状况、BMI范围等）
   - 例如：18-65岁健康成年人，肥胖女性，代谢综合征患者等
   - 答案必须是中文，不能出现英文单词如"men"、"women"等

2. **样本量**：研究中的参与者数量和类型
   - 例如：120名参与者，60例患者等
   - 答案必须是中文

3. **推荐补充剂量/用法**：研究中的MCT或相关营养素补充方案
   - 例如：每日30毫升MCT油，分2次服用；每餐前10克MCT等
   - 答案必须是中文，数字和单位要清晰

4. **作用机理**：MCT发挥效应的生物学机制
   - 例如：通过生酮作用促进脂肪燃烧；提高代谢率；抑制食欲等
   - 答案必须是中文，用科学术语描述

5. **摘要主要内容**：用1-2句话概括该研究的重点发现和结论
   - 例如：研究发现每日补充30毫升MCT油可以显著减少超重成年人的体脂含量
   - 答案必须是中文，简洁明了

6. **结论摘要**：研究的核心结论和研究意义，必须用中文表达
   - 例如：本研究表明MCT油补充剂能够有效改善肥胖人群的体重和体脂分布，为临床营养干预提供了新的证据支持
   - **强制性要求：答案必须是中文，不能使用英文** 
   - 如果摘要中没有明确结论，请基于研究结果总结中文结论

7. **国家**：研究进行所在的国家
   - 例如：美国、中国、英国、德国、日本、澳大利亚等
   - 只返回标准国家名称，如"USA"对应"美国"，"China"对应"中国"
   - 绝不能包含城市名（如Beijing、Shanghai、New York、London等）
   - 绝不能包含邮政编码（如H9X 3V9、M5V、V1M等）
   - 绝不能包含机构名称（如University、Hospital、Institute等）
   - 绝不能包含街道地址（如Street、Road、Avenue等）
   - 如果无法确定准确的国家，标注"需人工确认"

8. **数据收集年份**：研究实际数据收集的时间期间
   - 例如：2018年1月至12月，2019年6月-2020年5月，2020年等
   - 只返回具体年份或年份范围，不要包含发表年份
   - 如果摘要中没有明确提到数据收集时间，标注"未明确说明"

**请以JSON格式返回结果：**
```json
{{
  "研究对象": "提取的中文内容",
  "样本量": "提取的中文内容", 
  "推荐补充剂量/用法": "提取的中文内容",
  "作用机理": "提取的中文内容",
  "摘要主要内容": "提取的中文内容",
  "结论摘要": "提取的中文内容",
  "国家": "提取的中文内容",
  "数据收集年份": "提取的中文内容"
}}
```

**重要要求：**
- **结论摘要字段强制性要求：必须使用中文回答，不能包含任何英文内容**
- 所有答案必须是纯中文，不能包含英文单词
- **国家字段特别要求**：绝对不能返回城市、邮政编码、机构名称或地址信息
- **数据收集年份字段特别要求**：必须区分发表年份和数据收集年份，发表年份不是数据收集年份
- 只提取摘要中明确提到的信息，不要推断
- 如果信息不完整，使用"未明确说明"或"需人工确认"
- 返回格式必须是有效的JSON
"""
  
    # 尝试不同的API端点和模型组合
    model_configs = [
        # 端点, 模型名称
        ("gpt-3.5-turbo", API_ENDPOINTS[0]),  # GPTGod + gpt-3.5
        ("gpt-4", API_ENDPOINTS[0]),  # GPTGod + gpt-4
        ("deepseek-chat", API_ENDPOINTS[2])  # DeepSeek + deepseek-chat
    ]
    
    print("  🤖 AI模型开始分析摘要内容...")
    max_retries_per_config = 3  # 每个模型配置的最大重试次数
    
    for model_name, api_base_url in model_configs:
        for attempt in range(max_retries_per_config):
            # 从密钥池获取可用密钥
            current_api_key = api_key_pool.get_available_key()
            if not current_api_key:
                logger.error("没有可用的API密钥，尝试下一个模型")
                break
                
            headers = {
                "Authorization": f"Bearer {current_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            try:
                # 记录尝试信息（使用安全的日志记录）
                if API_KEY_POOL_CONFIG.get("log_key_usage", True):
                    key_id = api_key_pool._get_key_id(current_api_key)
                    logger.info(f"尝试使用模型 {model_name} 在端点 {api_base_url}，尝试 {attempt + 1}/{max_retries_per_config}，密钥 {key_id}")
                else:
                    logger.info(f"尝试使用模型 {model_name} 在端点 {api_base_url}，尝试 {attempt + 1}/{max_retries_per_config}")
                
                # 添加请求间隔，避免429错误
                time.sleep(REQUEST_DELAY)
                
                # 发送API请求
                response = requests.post(api_base_url, headers=headers, json=payload, timeout=30)
                
                # 处理API响应
                if response.status_code == 200:
                    result = response.json()
                    ai_content = result['choices'][0]['message']['content']
                    
                    # 记录成功信息
                    api_key_pool.report_success(current_api_key)
                    
                    if API_KEY_POOL_CONFIG.get("log_key_usage", True):
                        key_id = api_key_pool._get_key_id(current_api_key)
                        logger.info(f"AI API调用成功，模型：{model_name}，密钥：{key_id}")
                    else:
                        logger.info(f"AI API调用成功，模型：{model_name}")
                    
                    # 提取JSON部分
                    try:
                        # 尝试从AI响应中提取JSON
                        json_start = ai_content.find('{')
                        json_end = ai_content.rfind('}') + 1
                        if json_start != -1 and json_end != 0:
                            json_str = ai_content[json_start:json_end]
                            extracted_data = json.loads(json_str)
                            
                            # 验证提取的数据
                            validated_data = validate_extracted_data(extracted_data)
                            logger.info(f"成功提取信息")
                            return validated_data
                        else:
                            raise ValueError("未找到有效的JSON格式")
                            
                    except (json.JSONDecodeError, ValueError) as e:
                        # JSON解析失败也报告为失败，但不切换密钥
                        api_key_pool.report_failure(current_api_key, "json_parse_error")
                        logger.error(f"JSON解析失败：{e}")
                        continue  # 重试当前模型
                        
                elif response.status_code == 429:
                    # 请求频率过高
                    api_key_pool.report_failure(current_api_key, "rate_limit")
                    wait_time = REQUEST_DELAY * (2 ** attempt)  # 指数退避
                    logger.warning(f"API请求频率过高，模型：{model_name}，等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                    continue  # 重试当前模型
                    
                else:
                    # 其他HTTP错误
                    api_key_pool.report_failure(current_api_key, f"http_{response.status_code}")
                    logger.error(f"API请求失败，模型：{model_name}，状态码：{response.status_code}")
                    
                    # 如果是认证错误（401/403），直接切换密钥
                    if response.status_code in [401, 403]:
                        logger.warning(f"认证失败，切换到下一个密钥")
                        api_key_pool.rotate_key()
                        continue  # 尝试下一个密钥
                    else:
                        continue  # 重试当前模型
                    
            except requests.exceptions.RequestException as e:
                # 网络请求错误
                api_key_pool.report_failure(current_api_key, "network_error")
                logger.error(f"网络请求错误，模型：{model_name}，错误：{e}")
                continue  # 重试当前模型
                
            except Exception as e:
                # 其他异常
                api_key_pool.report_failure(current_api_key, "unknown_error")
                logger.error(f"AI信息提取过程发生错误，模型：{model_name}，错误：{e}")
                continue  # 重试当前模型
        
        # 当前模型配置的所有重试都失败，尝试下一个模型
        logger.warning(f"模型 {model_name} 在所有重试后仍然失败，尝试下一个模型")
    
    # 所有模型都失败
    logger.warning("所有AI模型和密钥组合都调用失败，使用备用数据")
    return get_fallback_data()

def validate_extracted_data(data: Dict[str, str]) -> Dict[str, str]:
    """
    验证和清理提取的数据
    """
    validated = {}
    for key in ["研究对象", "样本量", "推荐补充剂量/用法", "作用机理", "摘要主要内容", "结论摘要", "国家", "数据收集年份"]:
        value = data.get(key, "N/A")
        # 清理和验证值
        if isinstance(value, str):
            # 移除多余的空白字符
            value = value.strip()
            # 如果为空或包含无效内容，使用默认值
            if not value or value.lower() in ["null", "none", "", "undefined"]:
                value = "未明确说明"
        else:
            value = "未明确说明"
        validated[key] = value
    
    return validated

def get_fallback_data() -> Dict[str, str]:
    """
    当AI提取失败时返回的备用数据
    """
    return {
        "研究对象": "需人工确认",
        "样本量": "需人工确认", 
        "推荐补充剂量/用法": "需人工确认",
        "作用机理": "需人工确认",
        "摘要主要内容": "需人工确认",
        "结论摘要": "需人工确认",
        "国家": "需人工确认",
        "数据收集年份": "需人工确认"
    }

# ================= 全文提取功能 =================
def check_full_text_availability(pmid: str) -> Dict[str, any]:
    """
    检查PMID对应的文章是否提供免费全文
    重点检查title="Free full text at PubMed Central"的a元素
    
    Args:
        pmid: PubMed ID
    
    Returns:
        包含免费状态和链接信息的字典
    """
    try:
        # 构建PubMed页面URL
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        print(f"🔍 正在检查: {pubmed_url}")
        
        # 获取页面内容，添加更完整的请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(pubmed_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 优先级1：直接查找title="Free full text at PubMed Central"的a元素
        pmc_free_link = soup.find('a', title="Free full text at PubMed Central")
        if pmc_free_link:
            href = pmc_free_link.get('href', '')
            if href:
                full_url = href if href.startswith('http') else f"https://pubmed.ncbi.nlm.nih.gov{href}"
                print(f"✅ 找到PMC免费全文链接: {full_url}")
                return {
                    "is_free": True,
                    "pmid": pmid,
                    "pubmed_url": pubmed_url,
                    "links": [{
                        "url": full_url,
                        "title": "Free full text at PubMed Central",
                        "is_free": True,
                        "element_found": "title attribute"
                    }],
                    "message": "找到PMC免费全文",
                    "source": "direct_title_match"
                }
        
        # 优先级2：查找Full text links部分
        full_text_section = soup.find('div', {'data-content-id': 'full-text-links'})
        if not full_text_section:
            full_text_section = soup.find('div', class_='full-text-links')
        
        # 优先级3：在全文链接容器中查找免费链接
        free_links = []
        all_links = []
        
        if full_text_section:
            link_elements = full_text_section.find_all('a', href=True)
            print(f"📄 在全文链接部分找到 {len(link_elements)} 个链接")
        else:
            # 如果没有专门的全文链接部分，查找所有链接
            link_elements = soup.find_all('a', href=True)
            # 筛选可能相关的链接
            link_elements = [link for link in link_elements if any(keyword in link.get('href', '').lower() 
                               for keyword in ['pmc', 'europepmc', 'full', 'text', 'article'])]
            print(f"🔗 找到 {len(link_elements)} 个相关链接")
        
        # 分析每个链接
        for link in link_elements:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            title_attr = link.get('title', '')
            
            # 检查是否为免费链接
            is_free = False
            free_indicators = []
            
            # 检查各种免费指标
            if 'pmc' in href.lower():
                is_free = True
                free_indicators.append('PMC URL')
            if 'europepmc' in href.lower():
                is_free = True
                free_indicators.append('EuropePMC URL')
            if title_attr and 'free' in title_attr.lower():
                is_free = True
                free_indicators.append('Free title')
            if text and 'free' in text.lower():
                is_free = True
                free_indicators.append('Free text')
            if 'pubmedcentral' in href.lower():
                is_free = True
                free_indicators.append('PubMed Central')
            
            link_info = {
                "url": href if href.startswith('http') else f"https://pubmed.ncbi.nlm.nih.gov{href}",
                "title": text,
                "title_attr": title_attr,
                "is_free": is_free,
                "indicators": free_indicators
            }
            
            all_links.append(link_info)
            if is_free:
                free_links.append(link_info)
                print(f"✅ 发现免费链接: {text} - {link_info['url']} ({', '.join(free_indicators)})")
        
        # 确定最终结果
        if free_links:
            return {
                "is_free": True,
                "pmid": pmid,
                "pubmed_url": pubmed_url,
                "links": free_links,
                "all_links": all_links,
                "message": f"找到 {len(free_links)} 个免费全文链接",
                "source": "link_analysis"
            }
        else:
            # 如果没有找到免费链接，检查是否有付费链接
            has_paid_links = len(all_links) > 0
            return {
                "is_free": False,
                "pmid": pmid,
                "pubmed_url": pubmed_url,
                "links": all_links,
                "message": "未找到免费全文" + ("，但有付费链接" if has_paid_links else ""),
                "source": "no_free_links" if not has_paid_links else "paid_only"
            }
        
    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {str(e)}")
        return {
            "is_free": False,
            "pmid": pmid,
            "error": f"网络请求失败: {str(e)}",
            "message": "无法获取页面信息"
        }
    except Exception as e:
        print(f"❌ 解析失败: {str(e)}")
        return {
            "is_free": False,
            "pmid": pmid,
            "error": f"解析失败: {str(e)}",
            "message": "页面解析出错"
        }

def extract_full_text_content(pmid: str, link_url: str = None) -> Dict[str, any]:
    """
    从免费全文链接提取文章内容
    增强元素定位和内容提取逻辑
    
    Args:
        pmid: PubMed ID
        link_url: 全文链接URL，如果为None则自动查找
    
    Returns:
        包含提取内容的字典
    """
    try:
        # 如果没有提供链接URL，先检查可用性
        if not link_url:
            print(f"🔍 自动检测PMID {pmid}的免费全文链接...")
            availability = check_full_text_availability(pmid)
            if not availability['is_free']:
                return {
                    "success": False,
                    "pmid": pmid,
                    "message": availability['message']
                }
            
            # 查找第一个免费链接
            free_links = [link for link in availability['links'] if link['is_free']]
            if not free_links:
                return {
                    "success": False,
                    "pmid": pmid,
                    "message": "未找到可用的免费全文链接"
                }
            
            link_url = free_links[0]['url']
            print(f"📄 选择免费全文链接: {link_url}")
        
        print(f"📖 正在提取PMID {pmid}的全文内容...")
        
        # 获取全文页面，使用更完整的请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(link_url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 初始化提取结果
        content = {
            "pmid": pmid,
            "source_url": link_url,
            "extraction_success": False,
            "content": {},
            "debug_info": {
                "page_title": "",
                "total_sections": 0,
                "extracted_elements": []
            }
        }
        
        # 提取页面标题用于调试
        title_tag = soup.find('title')
        if title_tag:
            content['debug_info']['page_title'] = title_tag.get_text(strip=True)
            print(f"📄 页面标题: {title_tag.get_text(strip=True)[:100]}...")
        
        # 提取标题 - 多种选择器
        title_selectors = [
            'h1.article-title',
            'h1.title',
            'h1',
            '.article-title',
            '.title',
            'title'
        ]
        
        title_text = ""
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if title_text and len(title_text) > 10:  # 确保标题有意义
                    content['content']['title'] = title_text
                    content['debug_info']['extracted_elements'].append(f"标题: {selector}")
                    print(f"✅ 提取标题: {title_text[:100]}...")
                    break
        
        # 提取摘要 - 多种选择器策略
        abstract_selectors = [
            'div.abstract',
            'section.abstract',
            'div[data-section="abstract"]',
            'div#abstract',
            '.abstract-content',
            '.article-abstract',
            'div[class*="abstract"]'
        ]
        
        abstract_text = ""
        for selector in abstract_selectors:
            abstract_elem = soup.select_one(selector)
            if abstract_elem:
                # 移除不需要的元素
                for unwanted in abstract_elem.select('script, style, .reference, .citation'):
                    unwanted.decompose()
                
                abstract_text = abstract_elem.get_text(strip=True)
                if abstract_text and len(abstract_text) > 50:  # 确保摘要有意义
                    content['content']['abstract'] = abstract_text
                    content['debug_info']['extracted_elements'].append(f"摘要: {selector}")
                    print(f"✅ 提取摘要: {len(abstract_text)} 字符")
                    break
        
        # 提取关键词 - 多种位置
        keywords_selectors = [
            'div.keywords',
            'div#keywords',
            '.keyword-list',
            '[data-section="keywords"]',
            'p:contains("Keywords")',
            'div:contains("Keywords")'
        ]
        
        keywords_text = ""
        for selector in keywords_selectors:
            keywords_elem = soup.select_one(selector)
            if keywords_elem:
                keywords_text = keywords_elem.get_text(strip=True)
                if keywords_text and len(keywords_text) > 5:
                    content['content']['keywords'] = keywords_text
                    content['debug_info']['extracted_elements'].append(f"关键词: {selector}")
                    print(f"✅ 提取关键词: {keywords_text[:100]}...")
                    break
        
        # 提取作者信息
        authors_selectors = [
            'div.authors',
            'ul.author-list',
            '.author-list',
            'div.author-info',
            '[data-section="authors"]'
        ]
        
        authors_text = ""
        for selector in authors_selectors:
            authors_elem = soup.select_one(selector)
            if authors_elem:
                authors_text = authors_elem.get_text(strip=True)
                if authors_text and len(authors_text) > 10:
                    content['content']['authors'] = authors_text
                    content['debug_info']['extracted_elements'].append(f"作者: {selector}")
                    print(f"✅ 提取作者信息: {authors_text[:100]}...")
                    break
        
        # 提取正文内容 - 更智能的策略
        body_selectors = [
            'div.article-body',
            'article',
            'div.body-content',
            'div.main-content',
            'div.content',
            'div#content'
        ]
        
        body_text = ""
        for selector in body_selectors:
            body_elem = soup.select_one(selector)
            if body_elem:
                # 移除导航、广告、引用等不需要的内容
                unwanted_selectors = [
                    'script', 'style', 'nav', 'header', 'footer', 
                    '.advertisement', '.sidebar', '.related-articles',
                    '.reference', '.citation', '.author-notes'
                ]
                
                for unwanted_selector in unwanted_selectors:
                    for unwanted in body_elem.select(unwanted_selector):
                        unwanted.decompose()
                
                # 提取文本
                body_text = body_elem.get_text(strip=True)
                if body_text and len(body_text) > 200:  # 确保正文内容有意义
                    content['content']['body_text'] = body_text
                    content['debug_info']['extracted_elements'].append(f"正文: {selector}")
                    print(f"✅ 提取正文: {len(body_text)} 字符")
                    break
        
        # 提取参考文献
        refs_selectors = [
            'div.references',
            'ol.references',
            'ul.references',
            '.reference-list',
            '[data-section="references"]'
        ]
        
        refs_text = ""
        for selector in refs_selectors:
            refs_elem = soup.select_one(selector)
            if refs_elem:
                refs_text = refs_elem.get_text(strip=True)
                if refs_text and len(refs_text) > 50:
                    content['content']['references'] = refs_text
                    content['debug_info']['extracted_elements'].append(f"参考文献: {selector}")
                    print(f"✅ 提取参考文献: {len(refs_text)} 字符")
                    break
        
        # 统计提取的元素
        content['debug_info']['total_sections'] = len(content['content'])
        
        # 判断提取是否成功
        if len(content['content']) >= 2:  # 至少提取到标题和摘要
            content['extraction_success'] = True
            content['message'] = f"成功提取{len(content['content'])}个部分的内容"
            print(f"✅ 全文提取完成，共提取{len(content['content'])}个部分")
        else:
            content['extraction_success'] = False
            content['message'] = f"提取内容不完整，仅获取到{len(content['content'])}个部分"
            print(f"⚠️ 提取内容不完整，仅获取到{len(content['content'])}个部分")
        
        # 如果完全没有提取到内容，提供调试信息
        if not content['content']:
            content['extraction_success'] = False
            content['message'] = "未能提取到任何有效内容"
            content['debug_info']['no_content_reason'] = "页面可能需要特殊处理或链接无效"
            print(f"❌ 未能提取到任何有效内容")
        
        return content
        
    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {str(e)}")
        return {
            "success": False,
            "pmid": pmid,
            "error": f"网络请求失败: {str(e)}",
            "message": "无法获取全文页面",
            "debug_info": {"error_type": "network_error"}
        }
    except Exception as e:
        print(f"❌ 提取失败: {str(e)}")
        return {
            "success": False,
            "pmid": pmid,
            "error": f"提取失败: {str(e)}",
            "message": "内容提取出错",
            "debug_info": {"error_type": "extraction_error", "error_detail": str(e)}
        }

def analyze_pmid_with_full_text(pmid: str) -> Dict[str, any]:
    """
    综合分析PMID：检查免费状态并提取全文内容
    增强调试信息和错误处理
    
    Args:
        pmid: PubMed ID
    
    Returns:
        完整的分析结果
    """
    print(f"\n🔍 开始分析PMID: {pmid}")
    print("=" * 60)
    
    # 步骤1：检查全文可用性
    print("步骤1: 检查全文可用性...")
    availability = check_full_text_availability(pmid)
    
    # 初始化结果，包含parse_record需要的字段
    result = {
        "pmid": pmid,
        "timestamp": datetime.now().isoformat(),
        "is_free": availability.get('is_free', False),
        "links": availability.get('links', []),
        "message": availability.get('message', ''),
        "extraction_success": False,
        "extracted_content": {},
        "debug_info": {
            "availability_source": availability.get('source', 'unknown'),
            "total_links_found": len(availability.get('links', [])),
            "extraction_attempted": False,
            "extraction_details": {}
        }
    }
    
    if not availability.get('is_free', False):
        print(f"❌ PMID {pmid} 无免费全文: {availability.get('message', '未知原因')}")
        result['debug_info']['no_free_reason'] = availability.get('message', '未知原因')
        result['debug_info']['availability_source'] = availability.get('source', 'unknown')
        return result
    
    print(f"✅ PMID {pmid} 提供免费全文 (来源: {availability.get('source', 'unknown')})")
    result['debug_info']['extraction_attempted'] = True
    
    # 步骤2：提取全文内容
    print("\n步骤2: 提取全文内容...")
    try:
        full_text = extract_full_text_content(pmid)
        result['full_text_extraction'] = full_text
        
        # 更新调试信息
        if 'debug_info' in full_text:
            result['debug_info']['extraction_details'] = full_text['debug_info']
        
        if full_text.get('extraction_success', False):
            print(f"✅ 成功提取PMID {pmid}的全文内容")
            content_info = full_text.get('content', {})
            result['extraction_success'] = True
            result['extracted_content'] = content_info
            
            # 详细输出提取的内容信息
            print(f"   📄 标题: {content_info.get('title', 'N/A')[:100]}...")
            if 'abstract' in content_info:
                print(f"   📝 摘要: {len(content_info['abstract'])} 字符")
            if 'body_text' in content_info:
                print(f"   📖 正文: {len(content_info['body_text'])} 字符")
            if 'keywords' in content_info:
                print(f"   🔑 关键词: {len(content_info['keywords'])} 字符")
            if 'authors' in content_info:
                print(f"   👥 作者信息: {len(content_info['authors'])} 字符")
            if 'references' in content_info:
                print(f"   📚 参考文献: {len(content_info['references'])} 字符")
            
            # 统计提取的内容部分数
            content_parts = len([k for k, v in content_info.items() if v])
            print(f"   📊 总计提取了 {content_parts} 个内容部分")
            
        else:
            print(f"❌ PMID {pmid} 全文内容提取失败: {full_text.get('message', '未知错误')}")
            result['message'] = full_text.get('message', '提取失败')
            
            # 添加错误调试信息
            if 'error' in full_text:
                result['debug_info']['extraction_error'] = full_text['error']
                print(f"   🔍 错误详情: {full_text['error']}")
            
            if 'debug_info' in full_text and 'no_content_reason' in full_text['debug_info']:
                result['debug_info']['no_content_reason'] = full_text['debug_info']['no_content_reason']
                print(f"   🔍 失败原因: {full_text['debug_info']['no_content_reason']}")
    
    except Exception as e:
        print(f"❌ 全文提取过程出错: {str(e)}")
        result['message'] = f"全文提取过程出错: {str(e)}"
        result['debug_info']['extraction_error'] = str(e)
    
    print(f"\n📊 PMID {pmid} 分析完成")
    print(f"   - 免费全文: {'是' if result['is_free'] else '否'}")
    print(f"   - 提取成功: {'是' if result['extraction_success'] else '否'}")
    print("=" * 60)
    
    return result

# ================= 测试功能 =================
def test_ai_extraction():
    """
    测试混合信息提取功能的示例摘要
    """
    test_abstracts = [
        # 示例摘要1 - RCT研究
        """
        Background: Medium-chain triglycerides (MCT) have been proposed as a dietary supplement for weight management. 
        Objective: To evaluate the effects of MCT supplementation on body composition in overweight adults.
        Methods: We conducted a randomized controlled trial with 120 overweight participants (BMI 25-30 kg/m²) aged 25-55 years. 
        Participants received either 30ml MCT oil daily (n=60) or placebo (n=60) for 12 weeks. 
        Results: MCT group showed significant reductions in body fat mass (-2.3±0.8 kg vs -0.8±0.5 kg, p<0.001). 
        Mechanism: MCTs increase thermogenesis and promote fat oxidation through enhanced ketone production.
        Conclusions: Daily MCT supplementation effectively reduces body fat in overweight adults.
        """,
        
        # 示例摘要2 - Meta分析
        """
        Background: The efficacy of medium-chain triglycerides (MCT) for weight loss remains controversial.
        Objective: To systematically review and meta-analyze RCTs examining MCT effects on weight loss in adults.
        Methods: We searched databases for randomized controlled trials comparing MCT vs control interventions. 
        Eight studies involving 512 participants (age 18-65 years, various BMI ranges) were included.
        Dosage: MCT interventions ranged from 15-45ml daily for 4-24 weeks.
        Results: MCT supplementation significantly reduced body weight (-1.8 kg, 95% CI: -2.5 to -1.1 kg).
        Mechanisms: MCTs increase energy expenditure, enhance satiety, and promote ketogenesis.
        Conclusions: Strong evidence supports MCT use for moderate weight loss in adults.
        """,
        
        # 示例摘要3 - 机制研究
        """
        Background: Medium-chain triglycerides (MCT) may influence metabolic pathways differently than long-chain fatty acids.
        Objective: To investigate the metabolic mechanisms of MCT in human adipocytes.
        Methods: 80 healthy volunteers (40 men, 40 women, age 20-40 years) participated in this study. 
        Subjects consumed 20g MCT daily for 8 weeks. 
        Results: MCT increased resting metabolic rate by 8% and reduced appetite scores significantly.
        Mechanism: MCTs are rapidly oxidized, generating more ATP per gram than long-chain fatty acids, 
        and stimulate uncoupling proteins in brown adipose tissue.
        Conclusions: MCT enhances metabolic rate through enhanced thermogenesis and fat oxidation.
        """
    ]
    
    print("=" * 60)
    print("测试混合信息提取功能")
    print("=" * 60)
    
    for i, abstract in enumerate(test_abstracts, 1):
        print(f"\n测试摘要 {i}:")
        print("-" * 40)
        
        # 使用混合方法提取信息（主要：正则表达式，备用：AI）
        print("开始提取研究信息...")
        
        # 首先尝试正则表达式提取
        regex_extracted = extract_info_with_regex(abstract)
        print(f"正则表达式提取结果：{regex_extracted}")
        
        # 检查正则表达式提取结果的质量
        regex_quality = sum(1 for v in regex_extracted.values() if v != "未明确说明")
        print(f"正则表达式提取质量：{regex_quality}/4 字段有有效信息")
        
        # 如果正则表达式结果质量较低，尝试AI提取
        if regex_quality < 2:  # 如果少于2个字段有有效信息
            print("正则表达式提取结果质量较低，尝试AI提取...")
            ai_extracted = extract_info_with_ai(abstract)
            print(f"AI提取结果：{ai_extracted}")
            
            # 合并结果：优先使用AI结果，缺失时使用正则表达式结果
            final_extracted = {}
            for key in ["研究对象", "样本量", "推荐补充剂量/用法", "作用机理"]:
                ai_value = ai_extracted.get(key, "")
                regex_value = regex_extracted.get(key, "")
                
                if ai_value and ai_value not in ["N/A", "需人工确认", ""]:
                    final_extracted[key] = ai_value
                elif regex_value and regex_value != "未明确说明":
                    final_extracted[key] = regex_value
                else:
                    final_extracted[key] = "需人工确认"
        else:
            # 正则表达式结果质量较好，直接使用
            final_extracted = regex_extracted
            print("正则表达式提取结果质量良好，直接使用")
        
        # 显示最终结果
        print("最终提取结果:")
        for key, value in final_extracted.items():
            print(f"  {key}: {value}")
        
        print(f"\n摘要长度: {len(abstract)} 字符")
        time.sleep(2)  # 测试间隔
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


# ================= API密钥池测试函数 =================
def test_api_key_pool():
    """
    测试API密钥池管理器的各项功能
    包括密钥轮换、失败检测、禁用逻辑和统计信息
    """
    print("\n" + "=" * 70)
    print("API密钥池管理系统测试")
    print("=" * 70)
    
    # 创建测试用的密钥池配置
    test_keys = [
        "sk-test123456789abcdef",  # 密钥1
        "sk-test987654321fedcba",  # 密钥2
        "sk-test111111111111111"   # 密钥3
    ]
    
    test_config = {
        "max_failure_count": 2,        # 设置较低阈值用于测试
        "disable_duration": 10,        # 10秒禁用时间
        "success_reset_threshold": 1,
        "enable_key_rotation": True,
        "log_key_usage": True
    }
    
    # 创建测试密钥池管理器
    test_pool = APIKeyPoolManager(test_keys, test_config)
    print(f"✅ 创建测试密钥池，包含 {len(test_keys)} 个密钥")
    
    # 测试1: 基本密钥获取
    print("\n--- 测试1: 基本密钥获取 ---")
    key1 = test_pool.get_available_key()
    print(f"获取第一个可用密钥: {key1}")
    assert key1 == test_keys[0], "应该返回第一个密钥"
    
    # 测试2: 密钥轮换
    print("\n--- 测试2: 密钥轮换 ---")
    test_pool.rotate_key()
    key2 = test_pool.get_available_key()
    print(f"轮换后获取密钥: {key2}")
    assert key2 == test_keys[1], "应该返回第二个密钥"
    
    # 测试3: 失败计数和禁用
    print("\n--- 测试3: 失败计数和自动禁用 ---")
    initial_stats = test_pool.get_key_statistics()
    print(f"初始状态: {initial_stats}")
    
    # 报告失败直到触发禁用
    for i in range(test_config["max_failure_count"]):
        test_pool.report_failure(key1, "test_error")
        stats = test_pool.get_key_statistics()
        print(f"失败 {i+1} 次后: key_1 失败次数={stats['key_1']['failure_count']}")
    
    # 检查密钥是否被禁用
    key_after_failures = test_pool.get_available_key()
    print(f"禁用后获取的密钥: {key_after_failures}")
    assert key_after_failures == test_keys[1], "应该跳过禁用的密钥1"
    
    # 测试4: 成功重置失败计数
    print("\n--- 测试4: 成功重置失败计数 ---")
    test_pool.report_success(key2)
    stats = test_pool.get_key_statistics()
    print(f"成功后统计: key_2 成功={stats['key_2']['success_count']}, 失败={stats['key_2']['failure_count']}")
    
    # 测试5: 禁用恢复
    print("\n--- 测试5: 禁用恢复机制 ---")
    key1_stats_before = test_pool.get_key_statistics()['key_1']
    print(f"密钥1禁用状态: {key1_stats_before['is_disabled']}")
    
    if key1_stats_before['is_disabled']:
        print(f"等待禁用期结束 (当前配置: {test_config['disable_duration']}秒)")
        print("实际测试中，您可以设置更短的禁用时间进行快速测试")
        
        # 在实际测试中，我们可以模拟时间跳过
        # 这里我们手动重置禁用状态来演示
        test_pool.key_states['key_1']['is_disabled'] = False
        test_pool.key_states['key_1']['disabled_until'] = None
        print("手动重置禁用状态用于演示")
    
    # 测试6: 统计信息
    print("\n--- 测试6: 统计信息获取 ---")
    final_stats = test_pool.get_key_statistics()
    print("最终统计信息:")
    for key_id, stats in final_stats.items():
        print(f"  {key_id}:")
        print(f"    状态: {'禁用' if stats['is_disabled'] else '正常'}")
        print(f"    总请求: {stats['total_requests']}")
        print(f"    总成功: {stats['total_successes']}")
        print(f"    成功率: {stats['success_rate']:.2%}")
    
    # 测试7: 所有密钥都不可用的情况
    print("\n--- 测试7: 全部密钥禁用情况 ---")
    # 禁用所有密钥
    for i in range(len(test_keys)):
        key_id = f"key_{i+1}"
        test_pool.key_states[key_id]['is_disabled'] = True
        test_pool.key_states[key_id]['disabled_until'] = time.time() + 60
    
    no_key = test_pool.get_available_key()
    print(f"所有密钥禁用时获取结果: {no_key}")
    assert no_key is None, "应该返回None表示没有可用密钥"
    
    print("\n" + "=" * 70)
    print("API密钥池测试完成")
    print("=" * 70)
    
    return test_pool


def test_key_pool_scenarios():
    """
    测试密钥池在实际使用场景中的表现
    """
    print("\n" + "=" * 70)
    print("密钥池实际使用场景测试")
    print("=" * 70)
    
    # 使用实际的密钥池配置
    print(f"使用实际密钥池，包含 {len(API_KEYS_POOL)} 个密钥")
    
    # 显示密钥池统计信息
    stats = api_key_pool.get_key_statistics()
    print("当前密钥池状态:")
    for key_id, key_stats in stats.items():
        status = "🔴 禁用" if key_stats['is_disabled'] else "🟢 正常"
        last_used = "未使用" if not key_stats['last_used'] else time.strftime("%H:%M:%S", time.localtime(key_stats['last_used']))
        
        print(f"  {key_id}: {status}")
        print(f"    总请求: {key_stats['total_requests']}, 成功: {key_stats['total_successes']}")
        print(f"    成功率: {key_stats['success_rate']:.1%}")
        print(f"    最后使用: {last_used}")
    
    # 测试密钥获取
    print("\n--- 测试密钥获取 ---")
    available_key = api_key_pool.get_available_key()
    if available_key:
        key_id = api_key_pool._get_key_id(available_key)
        print(f"✅ 获取到可用密钥: {key_id}")
        
        # 模拟成功请求
        api_key_pool.report_success(available_key)
        print(f"✅ 报告密钥 {key_id} 请求成功")
        
        # 获取更新后的统计
        updated_stats = api_key_pool.get_key_statistics()[key_id]
        print(f"更新后成功率: {updated_stats['success_rate']:.1%}")
    else:
        print("❌ 没有可用的密钥")
    
    print("\n" + "=" * 70)
    print("实际场景测试完成")
    print("=" * 70)


def test_country_processing():
    """测试重构后的国家处理功能"""
    print("\n" + "=" * 70)
    print("重构后的国家处理功能测试")
    print("=" * 70)
    
    # 模拟article_data
    mock_articles = [
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Department of Cardiology, Johns Hopkins University, Baltimore, MD 21287, United States"
                }]
            }]
        },
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "School of Medicine, Peking University, Beijing, China"
                }]
            }]
        },
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Institute of Medical Sciences, University of Tokyo, Tokyo, Japan"
                }]
            }]
        },
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Random Hospital, Unknown City, Some Unknown Place"
                }]
            }]
        },
        {
            "AuthorList": [{}]  # 没有机构信息
        }
    ]
    
    print("测试缓存机制...")
    
    # 测试缓存功能
    result1 = extract_country_from_affiliation(mock_articles[0])
    print(f"第一次调用结果: {result1}")
    
    result2 = extract_country_from_affiliation(mock_articles[0])  # 相同的机构信息
    print(f"第二次调用结果 (缓存): {result2}")
    
    assert result1 == result2, "缓存应该返回相同结果"
    print("✓ 缓存机制测试通过")
    
    print("\n测试各种国家识别场景...")
    
    expected_results = ["United States", "China", "Japan", "需人工确认", "需人工确认"]
    
    for i, (article, expected) in enumerate(zip(mock_articles, expected_results)):
        result = extract_country_from_affiliation(article)
        print(f"测试案例 {i+1}: {result}")
        print(f"  预期结果: {expected}")
        print(f"  状态: {'✓ 通过' if result == expected else '✗ 不匹配'}")
    
    print("\n测试缓存统计信息...")
    print(f"当前缓存大小: {len(COUNTRY_CACHE)}")
    print("✓ 国家处理功能测试完成!")
    
    # 清理缓存
    COUNTRY_CACHE.clear()
    print("缓存已清理")


# 修改主程序以支持密钥池测试
if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_ai_extraction()
        elif sys.argv[1] == "test_key_pool":
            test_api_key_pool()
            test_key_pool_scenarios()
        elif sys.argv[1] == "test_country":
            test_country_processing()
        else:
            print("可用命令:")
            print("  python pubmed.py           - 运行正常程序")
            print("  python pubmed.py test      - 运行AI提取测试")
            print("  python pubmed.py test_key_pool - 运行密钥池测试")
            print("  python pubmed.py test_country - 运行国家处理测试")
    else:
        # 获取搜索词
        search_term = get_user_search_term()
        
        print(f"\n开始搜索: {search_term[:100]}...")
        
        # 1. 搜索
        ids = search_pubmed(search_term, MAX_RESULTS)
        
        if ids:
            print(f"找到 {len(ids)} 篇相关文献，开始获取详细信息...")
            
            # 2. 获取详情
            articles = fetch_details(ids)
            
            # 3. 解析数据
            results = []
            for i, article in enumerate(articles):
                print(f"正在处理文献 {i+1}/{len(articles)}...")
                results.append(parse_record(article))
            
            # 4. 生成表格
            df = pd.DataFrame(results)
            
            # 调整列顺序以符合文件要求
            columns_order = [
                '发表年份', '数据收集年份', '国家', '研究类型', '研究对象', '样本量', '推荐剂量', 
                '补充剂量/用法', '作用机理', '摘要主要内容', '证据等级', '结论摘要', '标题', 'PMID',
                # 全文相关字段
                '免费全文状态', '免费全文链接数', '全文提取状态', '全文内容摘要'
            ]
            # 确保所有列都存在
            for col in columns_order:
                if col not in df.columns:
                    if col in ['发表年份', '数据收集年份', '国家', '研究类型', '研究对象', '样本量', '推荐剂量', '补充剂量/用法', '作用机理', '摘要主要内容', '证据等级', '结论摘要', '标题']:
                        df[col] = "需人工确认"
                    elif col in ['免费全文状态', '免费全文链接数', '全文提取状态']:
                        df[col] = False if col in ['免费全文状态', '全文提取状态'] else 0
                    elif col == '全文内容摘要':
                        df[col] = "未启用全文提取"
                    elif col == 'PMID':
                        df[col] = ""
                    
            df = df[columns_order]
            
            # 导出
            filename = f"Literature_Search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\n✅ 成功导出表格：{filename}")
            print(f"📊 包含 {len(df)} 篇文献的详细信息")
        else:
            print("\n❌ 未找到相关文献，请检查搜索词是否正确")