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
API_KEY = "sk-1wLZqqkXDT9shZzgTqNRc0wNB6K4Kmu1t0kov0KA5I3auqVf"
ENABLE_WEB_SEARCH = True  # 是否启用web search功能
REQUEST_DELAY = 2.0  # API请求间隔（秒），避免429错误

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

    # 2. 数据收集年份 (通过AI提取)
    data['数据收集年份'] = ai_extracted.get('数据收集年份', "需人工确认")

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
    ai_extracted = extract_info_with_ai(abstract_text)
    logger.info(f"AI提取结果：{ai_extracted}")
    
    # 更新数据字段
    data['研究对象'] = ai_extracted.get('研究对象', "需人工确认")
    data['样本量'] = ai_extracted.get('样本量', "需人工确认")
    data['推荐补充剂量/用法'] = ai_extracted.get('推荐补充剂量/用法', "需人工确认")
    data['作用机理'] = ai_extracted.get('作用机理', "需人工确认")
    data['摘要主要内容'] = ai_extracted.get('摘要主要内容', "需人工确认")
    data['结论摘要'] = abstract_text # 保留原文摘要供参考
    
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
    从作者机构信息中提取国家名称
    
    Args:
        article_data: 从PubMed获取的文章数据
        
    Returns:
        国家名称字符串
    """
    # 预定义的国家列表（包含常见国家名称和变体）
    country_mappings = {
        # 北美洲
        "United States": "United States", "USA": "United States", "US": "United States", "America": "United States", "American": "United States",
        "Canada": "Canada", "Canadian": "Canada", 
        "Mexico": "Mexico", "Mexican": "Mexico",
        
        # 欧洲
        "United Kingdom": "United Kingdom", "UK": "United Kingdom", "Britain": "United Kingdom", "British": "United Kingdom", "England": "United Kingdom", "English": "United Kingdom", "Scotland": "United Kingdom", "Scottish": "United Kingdom", "Wales": "United Kingdom", "Welsh": "United Kingdom",
        "Germany": "Germany", "German": "Germany", "Deutschland": "Germany",
        "France": "France", "French": "France", 
        "Italy": "Italy", "Italian": "Italy",
        "Spain": "Spain", "Spanish": "Spain",
        "Netherlands": "Netherlands", "Dutch": "Netherlands",
        "Sweden": "Sweden", "Swedish": "Sweden",
        "Norway": "Norway", "Norwegian": "Norway",
        "Denmark": "Denmark", "Danish": "Denmark",
        "Finland": "Finland", "Finnish": "Finland",
        "Switzerland": "Switzerland", "Swiss": "Switzerland",
        "Austria": "Austria", "Austrian": "Austria",
        "Belgium": "Belgium", "Belgian": "Belgium",
        "Poland": "Poland", "Polish": "Poland",
        "Czech": "Czech Republic", "Czechia": "Czech Republic",
        "Portugal": "Portugal", "Portuguese": "Portugal",
        "Greece": "Greece", "Greek": "Greece",
        "Russia": "Russia", "Russian": "Russia",
        
        # 亚洲
        "China": "China", "Chinese": "China", "Beijing": "China", "Shanghai": "China", "Guangzhou": "China", "Shenzhen": "China",
        "Japan": "Japan", "Japanese": "Japan", "Tokyo": "Japan", "Osaka": "Japan",
        "Korea": "South Korea", "Korean": "South Korea", "Seoul": "South Korea",
        "South Korea": "South Korea", 
        "India": "India", "Indian": "India", "Mumbai": "India", "Delhi": "India",
        "Singapore": "Singapore", "Singaporean": "Singapore",
        "Thailand": "Thailand", "Thai": "Thailand",
        "Malaysia": "Malaysia", "Malaysian": "Malaysia",
        "Indonesia": "Indonesia", "Indonesian": "Indonesia",
        "Philippines": "Philippines", "Philippine": "Philippines",
        "Vietnam": "Vietnam", "Vietnamese": "Vietnam",
        "Taiwan": "Taiwan", "Taiwanese": "Taiwan",
        "Hong Kong": "Hong Kong",
        
        # 大洋洲
        "Australia": "Australia", "Australian": "Australia", "Sydney": "Australia", "Melbourne": "Australia",
        "New Zealand": "New Zealand", "NZ": "New Zealand", "Auckland": "New Zealand",
        
        # 非洲
        "South Africa": "South Africa", "Egypt": "Egypt", "Egyptian": "Egypt",
        "Nigeria": "Nigeria", "Ghana": "Ghana", "Kenya": "Kenya",
        
        # 南美洲
        "Brazil": "Brazil", "Brazilian": "Brazil", "Argentina": "Argentina", "Chile": "Chile", "Colombia": "Colombia"
    }
    
    # 需要过滤的非国家词汇
    invalid_country_indicators = [
        # 城市和地区
        "street", "st.", "avenue", "ave.", "road", "rd.", "boulevard", "blvd.",
        "hospital", "university", "college", "institute", "school", "department",
        "center", "centre", "laboratory", "lab", "building", "floor", "room",
        "zip", "postal", "postcode", "code", "district", "province", "state",
        # 邮政编码格式
        r'\d{5}(-\d{4})?', r'[A-Z]\d[A-Z] \d[A-Z]\d', r'\d{4}-\d{3}', r'\d{3}\s?\d{3}',
        # 特殊格式
        "H9X", "M5V", "V1M", "SW3P", "WC1N", "1A1", "2B2"
    ]
    
    try:
        # 尝试从第一作者提取机构信息
        if 'AuthorList' not in article_data or not article_data['AuthorList']:
            return "需人工确认"
            
        first_author = article_data['AuthorList'][0]
        
        # 获取机构信息
        affiliation = ""
        if 'AffiliationInfo' in first_author and first_author['AffiliationInfo']:
            affiliation = first_author['AffiliationInfo'][0].get('Affiliation', '')
        elif 'Affiliation' in first_author:
            affiliation = first_author['Affiliation']
        
        if not affiliation:
            return "需人工确认"
        
        logger.info(f"提取到的机构信息: {affiliation[:200]}...")
        
        # 清理机构信息
        affiliation = affiliation.replace('\n', ' ').replace('\r', ' ')
        affiliation_parts = [part.strip() for part in affiliation.split(',')]
        
        # 提取国家关键词
        country_candidates = []
        
        # 检查每个部分是否包含国家信息
        logger.info(f"机构信息分割后: {affiliation_parts}")
        
        for part in affiliation_parts:
            part_upper = part.upper().strip()
            part_lower = part.lower().strip()
            
            logger.info(f"检查部分: '{part}' -> 上: '{part_upper}' -> 下: '{part_lower}'")
            
            # 先检查是否匹配已知国家
            matched_country = None
            for country_key, country_name in country_mappings.items():
                if (country_key.upper() in part_upper or 
                    country_key.lower() in part_lower):
                    logger.info(f"匹配到国家关键词: '{country_key}' -> '{country_name}'")
                    matched_country = country_name
                    break
            
            if matched_country:
                country_candidates.append(matched_country)
                logger.info(f"添加到候选国家列表: {matched_country}")
                continue
                
            # 如果没有匹配到已知国家，再检查是否包含无效指标
            is_invalid = False
            for invalid in invalid_country_indicators:
                if isinstance(invalid, str):
                    if invalid.lower() in part_lower:
                        is_invalid = True
                        break
                else:  # 正则表达式
                    if invalid.search(part):
                        is_invalid = True
                        break
            
            if is_invalid:
                continue
        
        # 如果找到国家候选，返回最可能的
        if country_candidates:
            # 优先返回United States或China（最常见），否则返回第一个
            for priority_country in ["United States", "China", "United Kingdom", "Germany", "Japan", "Australia"]:
                if priority_country in country_candidates:
                    return priority_country
            return country_candidates[0]
        
        # 如果没有找到预定义国家，尝试智能提取
        # 提取最后一个逗号分隔的部分（通常是国家）
        potential_country = affiliation_parts[-1].strip()
        
        # 验证提取的国家是否有效
        if is_likely_country(potential_country):
            return potential_country
        
        return "需人工确认"
        
    except Exception as e:
        logger.error(f"提取国家信息时出错: {e}")
        return "需人工确认"

def is_likely_country(text: str) -> bool:
    """
    验证提取的文本是否可能是国家名称
    
    Args:
        text: 待验证的文本
        
    Returns:
        布尔值，表示是否是可能的国家名称
    """
    if not text or len(text.strip()) < 2:
        return False
    
    text = text.strip()
    
    # 长度限制（国家名称通常2-30个字符）
    if len(text) < 2 or len(text) > 30:
        return False
    
    # 不能包含数字（邮政编码）
    if any(char.isdigit() for char in text):
        return False
    
    # 不能包含常见的非国家词汇
    invalid_patterns = [
        r'\d+',  # 包含数字
        r'^\d',  # 以数字开头
        r'\d$',  # 以数字结尾
        r'[A-Z]\d[A-Z]',  # 邮政编码格式
        r'\d[A-Z]\d',  # 邮政编码格式
        r'(street|st\.?|avenue|ave\.?|road|rd\.?)',  # 街道
        r'(hospital|university|college|institute)',  # 机构
        r'(zip|postal|postcode)',  # 邮政编码
        r'(building|floor|room)',  # 建筑信息
    ]
    
    import re
    for pattern in invalid_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    # 检查是否匹配常见的国家名称格式
    country_patterns = [
        r'^[A-Z][a-z]+$',  # 首字母大写，如"Germany"
        r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # 两个词，如"New Zealand"
        r'^[A-Z]+$',  # 全大写，如"USA"
        r'^[A-Z][a-z]+$',  # 标准国家名格式
    ]
    
    for pattern in country_patterns:
        if re.match(pattern, text):
            return True
    
    return False

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
            "国家": "需人工确认",
            "数据收集年份": "需人工确认"
        }
    
    # 构建全中文提示词，要求AI从摘要中提取特定信息
    prompt = f"""
请分析以下英文学术文献摘要，并提取以下七个方面的中文信息：

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

6. **国家**：研究进行所在的国家
   - 例如：美国、中国、英国、德国、日本、澳大利亚等
   - 只返回标准国家名称，如"USA"对应"美国"，"China"对应"中国"
   - 绝不能包含城市名（如Beijing、Shanghai、New York、London等）
   - 绝不能包含邮政编码（如H9X 3V9、M5V、V1M等）
   - 绝不能包含机构名称（如University、Hospital、Institute等）
   - 绝不能包含街道地址（如Street、Road、Avenue等）
   - 如果无法确定准确的国家，标注"需人工确认"

7. **数据收集年份**：研究实际数据收集的时间期间
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
  "国家": "提取的中文内容",
  "数据收集年份": "提取的中文内容"
}}
```

**重要要求：**
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
    
    for model_name, api_base_url in model_configs:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
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
            logger.info(f"尝试使用模型 {model_name} 在端点 {api_base_url}，摘要长度：{len(abstract_text)}字符")
            
            # 添加请求间隔，避免429错误
            time.sleep(REQUEST_DELAY)
            
            # 发送API请求
            response = requests.post(api_base_url, headers=headers, json=payload, timeout=30)
            
            # 处理API响应
            if response.status_code == 200:
                result = response.json()
                ai_content = result['choices'][0]['message']['content']
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
                        logger.info(f"成功提取信息：{validated_data}")
                        return validated_data
                    else:
                        raise ValueError("未找到有效的JSON格式")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"JSON解析失败：{e}，AI响应：{ai_content}")
                    continue  # 尝试下一个模型
                    
            elif response.status_code == 429:
                logger.warning(f"API请求频率过高，模型：{model_name}")
                time.sleep(REQUEST_DELAY * 5)  # 等待更长时间
                continue  # 尝试下一个模型
                
            else:
                logger.error(f"API请求失败，模型：{model_name}，状态码：{response.status_code}")
                continue  # 尝试下一个模型
                
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误，模型：{model_name}，错误：{e}")
            continue  # 尝试下一个模型
        except Exception as e:
            logger.error(f"AI信息提取过程发生错误，模型：{model_name}，错误：{e}")
            continue  # 尝试下一个模型
    
    # 所有模型都失败
    logger.warning("所有AI模型都调用失败，使用备用数据")
    return get_fallback_data()

def validate_extracted_data(data: Dict[str, str]) -> Dict[str, str]:
    """
    验证和清理提取的数据
    """
    validated = {}
    for key in ["研究对象", "样本量", "推荐补充剂量/用法", "作用机理", "摘要主要内容", "国家", "数据收集年份"]:
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

# ================= 主程序 =================
def get_user_search_term():
    """
    获取用户输入的搜索词
    """
    global MAX_RESULTS, ENABLE_FULLTEXT_EXTRACTION
    
    print("\n" + "="*60)
    print("PubMed文献搜索工具")
    print("="*60)
    
    print("\n当前配置:")
    print(f"默认搜索词: {SEARCH_TERM.strip()[:100]}...")
    print(f"最大结果数: {MAX_RESULTS}")
    print(f"全文提取功能: {'开启' if ENABLE_FULLTEXT_EXTRACTION else '关闭'}")
    print(f"邮箱: {Entrez.email}")
    
    print("\n请选择操作:")
    print("1. 使用默认搜索词开始搜索")
    print("2. 输入新的搜索词")
    print("3. 查看详细搜索词")
    print("4. 设置最大结果数量")
    print("5. 启用/禁用全文提取功能")
    print("6. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == "1":
            return SEARCH_TERM
        elif choice == "2":
            print("\n请输入搜索词 (支持PubMed语法):")
            print("示例: (diabetes OR diabetes mellitus) AND (metformin OR insulin)")
            print("或者直接按Enter使用默认搜索词")
            
            custom_search = input("搜索词: ").strip()
            if custom_search:
                return custom_search
            else:
                return SEARCH_TERM
        elif choice == "3":
            print(f"\n当前默认搜索词:")
            print("-"*40)
            print(SEARCH_TERM)
            print("-"*40)
            continue
        elif choice == "4":
            print(f"\n当前最大结果数量: {MAX_RESULTS}")
            print("建议值：20-500（数字越大搜索时间越长）")
            
            try:
                new_max = input("请输入新的最大结果数量 (直接按Enter保持当前值): ").strip()
                if new_max:
                    new_max_num = int(new_max)
                    if new_max_num > 0:
                        MAX_RESULTS = new_max_num
                        print(f"✅ 最大结果数量已更新为: {MAX_RESULTS}")
                    else:
                        print("❌ 请输入大于0的数字")
                else:
                    print(f"✅ 保持当前值: {MAX_RESULTS}")
            except ValueError:
                print("❌ 请输入有效的数字")
            continue
        elif choice == "5":
            ENABLE_FULLTEXT_EXTRACTION = not ENABLE_FULLTEXT_EXTRACTION
            status = "已启用" if ENABLE_FULLTEXT_EXTRACTION else "已禁用"
            print(f"\n全文提取功能: {status}")
            print(f"当前状态: {'开启' if ENABLE_FULLTEXT_EXTRACTION else '关闭'}")
            continue
        elif choice == "6":
            print("程序退出")
            exit(0)
        else:
            print("无效选择，请输入 1-6")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数，如果是 "test" 则运行测试
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_ai_extraction()
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
                '发表年份', '数据收集年份', '国家', '研究类型', 
                '研究对象', '样本量', '推荐补充剂量/用法', 
                '作用机理', '摘要主要内容', '证据等级', '结论摘要', '标题', 'PMID',
                # 全文相关字段
                '免费全文状态', '免费全文链接数', '全文提取状态', '全文内容摘要'
            ]
            # 确保所有列都存在
            for col in columns_order:
                if col not in df.columns:
                    if col == '摘要主要内容':
                        df[col] = "需人工确认"
                    elif col in ['免费全文状态', '免费全文链接数', '全文提取状态']:
                        df[col] = False if col in ['免费全文状态', '全文提取状态'] else 0
                    elif col == '全文内容摘要':
                        df[col] = "未启用全文提取"
                    else:
                        df[col] = ""
                    
            df = df[columns_order]
            
            # 导出
            filename = f"Literature_Search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\n✅ 成功导出表格：{filename}")
            print(f"📊 包含 {len(df)} 篇文献的详细信息")
        else:
            print("\n❌ 未找到相关文献，请检查搜索词是否正确")