"""
数据解析模块 - 负责从PubMed数据中提取和解析结构化信息
"""
import re
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class DataParser:
    """PubMed数据解析器"""
    
    def __init__(self):
        # 研究类型识别模式
        self.research_patterns = {
            'RCT': [
                r'randomized controlled trial',
                r'randomised controlled trial',
                r'RCT',
                r'placebo-controlled',
                r'double-blind',
                r'single-blind'
            ],
            'Meta-analysis': [
                r'meta-analysis',
                r'meta analysis',
                r'systematic review',
                r'pooled analysis'
            ],
            'Observational': [
                r'cohort',
                r'cross-sectional',
                r'case-control',
                r'longitudinal',
                r'prospective',
                r'retrospective'
            ],
            'Review': [
                r'review',
                r'overview',
                r'summary'
            ],
            'Mechanism': [
                r'mechanism',
                r'pathway',
                r'metabolic',
                r'biochemical'
            ]
        }
        
        # 样本量提取模式
        self.sample_size_patterns = [
            r'(\d+)\s+(?:participants|subjects|patients|cases)',
            r'n\s*=\s*(\d+)',
            r'with\s+(\d+)\s+(?:participants|subjects)',
            r'(\d+)\s+(?:healthy\s+)?(?:adults?|men|women)',
            r'study\s+(?:with\s+)?(\d+)',
            r'total\s+of\s+(\d+)'
        ]
        
        # 剂量信息模式
        self.dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(ml|mL|milliliters?)',
            r'(\d+(?:\.\d+)?)\s*(g|grams?)',
            r'(\d+(?:\.\d+)?)\s*(mg|milligrams?)',
            r'daily\s+(\d+(?:\.\d+)?)\s*(ml|mL)',
            r'(\d+(?:\.\d+)?)\s*(?:×|x)\s*(\d+)\s*(?:times?|次)',
            r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(?:ml|mL)'
        ]
        
        # 持续时间模式
        self.duration_patterns = [
            r'for\s+(\d+)\s+(weeks?|months?|days?)',
            r'(\d+)\s+(?:week|month|day)\s+(?:study|trial|period)',
            r'(\d+)\s+(?:weeks?|months?|days?)\s+(?:of|intervention)',
            r'over\s+(\d+)\s+(?:weeks?|months?)'
        ]

    def extract_research_type(self, abstract: str, title: str = "") -> str:
        """
        从摘要和标题中识别研究类型
        
        该方法使用预定义的正则表达式模式来识别文献的研究设计类型，
        包括随机对照试验(RCT)、Meta分析、观察性研究、综述等类型。
        
        Args:
            abstract (str): 文献摘要文本
            title (str, optional): 文献标题，默认为空字符串
        
        Returns:
            str: 研究类型字符串，可能的值包括:
                 - "RCT": 随机对照试验
                 - "Meta-analysis": Meta分析/系统综述  
                 - "Observational": 观察性研究
                 - "Review": 综述
                 - "Mechanism": 机制研究
                 - "Other": 其他类型
        """
        # 将标题和摘要合并并转为小写，便于模式匹配
        text = (title + " " + abstract).lower()
        
        # 遍历预定义的研究类型和对应的模式列表
        for research_type, patterns in self.research_patterns.items():
            for pattern in patterns:
                # 使用正则表达式进行不区分大小写的匹配
                if re.search(pattern, text, re.IGNORECASE):
                    return research_type
        
        return "Other"

    def extract_sample_size(self, abstract: str) -> Dict[str, Any]:
        """
        从摘要中提取样本量信息
        
        该方法使用多种正则表达式模式来识别和提取文献中的样本量数据，
        包括研究对象的数量(n=)、范围(如n=20-30)、具体数值等。
        
        Args:
            abstract (str): 文献摘要文本
        
        Returns:
            Dict[str, Any]: 包含样本量信息的字典，包括:
                - extracted (bool): 是否成功提取到样本量信息
                - sample_size (int or None): 提取的样本量数值
                - pattern_matched (str or None): 匹配到的模式类型
                - raw_text (str or None): 匹配的原始文本片段
        """
        # 移除可能的缩进和格式化符号
        clean_text = abstract.replace('\n', ' ').replace('\r', ' ')
        
        # 遍历样本量模式进行匹配
        for pattern in self.sample_size_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                return {
                    "extracted": True,
                    "sample_size": int(match.group(1)),
                    "pattern_matched": "sample_size_pattern",
                    "raw_text": match.group(0)
                }
        
        # 如果没有找到匹配的样本量模式，返回默认值
        return {
            "extracted": False,
            "sample_size": None,
            "pattern_matched": None,
            "raw_text": None
        }

    def extract_dosage_info(self, abstract: str, title: str = "") -> str:
        """提取剂量信息"""
        text = title + " " + abstract
        
        dosages = []
        for pattern in self.dosage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dosages.append(match.group(0))
        
        if dosages:
            return "; ".join(dosages[:2])  # 最多返回2个剂量信息
        
        return "未明确说明"

    def extract_duration(self, abstract: str, title: str = "") -> str:
        """提取研究持续时间"""
        text = title + " " + abstract
        
        for pattern in self.duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} {match.group(2)}"
        
        return "未明确说明"

    def extract_population_info(self, abstract: str, title: str = "") -> str:
        """提取人群信息"""
        text = title + " " + abstract
        
        # 年龄模式
        age_patterns = [
            r'(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*years?\s*old',
            r'(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*y',
            r'aged\s+(\d{1,2})\s*(?:to|-)\s*(\d{1,2})',
            r'(\d{1,2})\s*-\s*(\d{1,2})\s*years?'
        ]
        
        # BMI模式
        bmi_patterns = [
            r'BMI\s+(\d{1,2}(?:\.\d+)?)\s*(?:to|-)\s*(\d{1,2}(?:\.\d+)?)',
            r'(\d{1,2}(?:\.\d+)?)\s*≤\s*BMI\s*≤\s*(\d{1,2}(?:\.\d+)?)'
        ]
        
        population_info = []
        
        # 提取年龄信息
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                population_info.append(f"{match.group(1)}-{match.group(2)}岁")
                break
        
        # 提取BMI信息
        for pattern in bmi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                population_info.append(f"BMI {match.group(1)}-{match.group(2)}")
                break
        
        # 提取健康状态
        if re.search(r'overweight|obese', text, re.IGNORECASE):
            population_info.append("超重/肥胖人群")
        elif re.search(r'healthy', text, re.IGNORECASE):
            population_info.append("健康人群")
        elif re.search(r'metabolic', text, re.IGNORECASE):
            population_info.append("代谢异常人群")
        
        if population_info:
            return "; ".join(population_info)
        
        return "未明确说明"

    def parse_pubmed_record(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析PubMed记录数据"""
        try:
            # 提取基本信息
            pmid = article_data.get('PMID', 'N/A')
            title = ""
            abstract = ""
            
            # 获取标题
            if 'ArticleTitle' in article_data:
                title = str(article_data['ArticleTitle'])
            elif 'Title' in article_data:
                title = str(article_data['Title'])
            
            # 获取摘要
            abstract_text = ""
            if 'Abstract' in article_data and 'AbstractText' in article_data['Abstract']:
                abstract_text = str(article_data['Abstract']['AbstractText'])
            elif 'AbstractText' in article_data:
                abstract_text = str(article_data['AbstractText'])
            
            # 标准化摘要格式
            if isinstance(abstract_text, list):
                abstract_text = ' '.join([str(x) for x in abstract_text])
            
            abstract = abstract_text
            
            # 提取发表信息
            pub_year = "N/A"
            pub_month = "N/A"
            
            if 'PubDate' in article_data:
                pub_date = article_data['PubDate']
                if 'Year' in pub_date:
                    pub_year = str(pub_date['Year'])
                if 'Month' in pub_date:
                    pub_month = str(pub_date['Month'])
            elif 'DP' in article_data:
                dp_text = str(article_data['DP'])
                year_match = re.search(r'(\d{4})', dp_text)
                if year_match:
                    pub_year = year_match.group(1)
            
            # 提取期刊信息
            journal = "N/A"
            if 'Journal' in article_data and 'Title' in article_data['Journal']:
                journal = str(article_data['Journal']['Title'])
            elif 'JT' in article_data:
                journal = str(article_data['JT'])
            
            # 提取作者信息
            authors = []
            if 'AuthorList' in article_data:
                for author in article_data['AuthorList']:
                    if 'LastName' in author and 'ForeName' in author:
                        authors.append(f"{author['LastName']} {author['ForeName']}")
                    elif 'LastName' in author:
                        authors.append(author['LastName'])
                    elif 'CollectiveName' in author:
                        authors.append(author['CollectiveName'])
            
            # 提取DOI
            doi = "N/A"
            if 'ELocationID' in article_data:
                for eloc in article_data['ELocationID']:
                    if eloc.get('EIdType') == 'doi':
                        doi = str(eloc.get('EIdValue', 'N/A'))
                        break
            elif 'DOI' in article_data:
                doi = str(article_data['DOI'])
            
            # 提取MeSH术语
            mesh_terms = []
            if 'MeshHeadingList' in article_data:
                for mesh in article_data['MeshHeadingList']:
                    if 'DescriptorName' in mesh:
                        mesh_terms.append(str(mesh['DescriptorName']))
            elif 'MH' in article_data:
                mesh_terms = [str(x) for x in article_data['MH']]
            
            # 提取关键词
            keywords = []
            if 'KeywordList' in article_data:
                for keyword in article_data['KeywordList']:
                    if isinstance(keyword, dict) and 'Keyword' in keyword:
                        keywords.append(str(keyword['Keyword']))
                    else:
                        keywords.append(str(keyword))
            elif 'TI' in article_data:
                keywords = [str(x) for x in article_data['TI']]
            
            # 构建解析结果
            parsed_record = {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'publication_year': pub_year,
                'publication_month': pub_month,
                'journal': journal,
                'authors': authors,
                'doi': doi,
                'mesh_terms': mesh_terms,
                'keywords': keywords,
                'author_count': len(authors),
                'abstract_length': len(abstract) if abstract else 0,
                'has_full_text': False,  # 这个字段会在后续处理中更新
                'parsed_timestamp': None  # 这个字段会在后续处理中更新
            }
            
            return parsed_record
            
        except Exception as e:
            logger.error(f"解析PubMed记录时出错: {e}")
            return {
                'pmid': 'N/A',
                'title': '解析失败',
                'abstract': '',
                'error': str(e)
            }

    def extract_structured_info(self, abstract: str, title: str = "") -> Dict[str, str]:
        """
        使用正则表达式提取结构化信息
        
        这是DataParser的核心方法，它调用各种子方法来提取文献中的结构化信息，
        包括研究对象、样本量、剂量信息、持续时间和研究类型等关键数据。
        
        Args:
            abstract (str): 文献摘要文本
            title (str, optional): 文献标题，默认为空字符串
        
        Returns:
            Dict[str, str]: 包含结构化信息的字典，包括以下键值:
                - '研究对象': 提取的研究人群信息
                - '样本量': 提取的样本量信息（注意：这里直接返回字符串格式）
                - '推荐补充剂量/用法': 提取的剂量和用药信息
                - '研究持续时间': 提取的研究持续时间
                - '研究类型': 识别出的研究设计类型
        
        Note:
            该方法会自动验证提取的信息，如果某项信息为空或空白，
            则会返回默认值"未明确说明"，如果遇到解析错误，
            则返回"需人工确认"。
        """
        try:
            info = {
                '研究对象': self.extract_population_info(abstract, title),
                '样本量': self.extract_sample_size(abstract, title),
                '推荐补充剂量/用法': self.extract_dosage_info(abstract, title),
                '研究持续时间': self.extract_duration(abstract, title),
                '研究类型': self.extract_research_type(abstract, title)
            }
            
            # 验证提取的信息
            for key, value in info.items():
                if not value or value.strip() == "":
                    info[key] = "未明确说明"
            
            return info
            
        except Exception as e:
            logger.error(f"提取结构化信息时出错: {e}")
            return {
                '研究对象': "需人工确认",
                '样本量': "需人工确认",
                '推荐补充剂量/用法': "需人工确认",
                '研究持续时间': "需人工确认",
                '研究类型': "需人工确认"
            }


# 创建全局解析器实例
data_parser = DataParser()


# 向后兼容的便捷函数
def extract_info_with_regex(abstract_text: str, title: str = "") -> Dict[str, str]:
    """
    使用正则表达式从摘要中提取结构化信息（保持向后兼容）
    """
    return data_parser.extract_structured_info(abstract_text, title)


def parse_record(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析PubMed记录（保持向后兼容）
    """
    return data_parser.parse_pubmed_record(article_data)