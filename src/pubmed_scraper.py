"""
PubMed数据获取模块
负责PubMed搜索和文献详情获取功能
"""

import logging
from Bio import Entrez
from typing import List, Dict, Any

# 导入配置管理器
from src.config import config_manager

logger = logging.getLogger(__name__)

class PubMedScraper:
    """
    PubMed文献搜索和抓取器
    
    该类提供了与PubMed数据库交互的功能，包括搜索文献、获取详情信息、
    以及批量处理文献数据。支持多种搜索策略和结果处理方式。
    
    主要功能：
    - 关键词搜索文献
    - 获取文献详细信息
    - 搜索并获取详情的一体化操作
    - 提取文献基本信息
    
    属性:
        email (str): 联系邮箱，用于PubMed API
        config (ConfigManager): 配置管理器实例
        max_results (int): 最大搜索结果数
        delay (float): 请求间隔时间
        logger: 日志记录器
    """
    
    def __init__(self, email: str = None):
        """
        初始化PubMed抓取器
        
        Args:
            email: 联系邮箱，用于PubMed API
        """
        self.email = email or config_manager.get("entrez_email", "varian69@gmail.com")
        Entrez.email = self.email
        logger.info(f"PubMed抓取器已初始化，联系邮箱: {self.email}")
    
    def search(self, query: str, max_results: int = 20) -> List[str]:
        """
        在PubMed中搜索并返回ID列表
        
        Args:
            query: 搜索查询词
            max_results: 最大结果数
            
        Returns:
            PubMed ID列表
        """
        logger.info(f"正在搜索: {query.strip()}")
        try:
            handle = Entrez.esearch(
                db="pubmed", 
                term=query, 
                retmax=max_results, 
                sort="relevance"
            )
            record = Entrez.read(handle)
            handle.close()
            
            id_list = record.get("IdList", [])
            logger.info(f"搜索完成，找到 {len(id_list)} 个结果")
            return id_list
            
        except Exception as e:
            logger.error(f"PubMed搜索失败: {e}")
            return []
    
    def fetch_details(self, id_list: List[str]) -> List[Dict[str, Any]]:
        """
        根据ID获取文献详细信息
        
        Args:
            id_list: PubMed ID列表
            
        Returns:
            文献详细信息列表
        """
        if not id_list:
            logger.warning("没有提供PMID列表")
            return []
            
        logger.info(f"正在获取 {len(id_list)} 篇文献的详细信息")
        ids = ",".join(id_list)
        
        try:
            handle = Entrez.efetch(
                db="pubmed", 
                id=ids, 
                retmode="xml"
            )
            records = Entrez.read(handle)
            handle.close()
            
            articles = records.get('PubmedArticle', [])
            logger.info(f"成功获取 {len(articles)} 篇文献详情")
            return articles
            
        except Exception as e:
            logger.error(f"获取文献详情失败: {e}")
            return []
    
    def search_with_details(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        搜索并直接获取详细信息
        
        Args:
            query: 搜索查询词
            max_results: 最大结果数
            
        Returns:
            文献详细信息列表
        """
        # 执行搜索
        id_list = self.search(query, max_results)
        if not id_list:
            return []
        
        # 获取详细信息
        articles = self.fetch_details(id_list)
        return articles
    
    def get_article_basic_info(self, article: Dict[str, Any]) -> Dict[str, str]:
        """
        提取文献基本信息
        
        Args:
            article: PubMed文献记录
            
        Returns:
            基本信息字典
        """
        info = {}
        
        try:
            medline = article['MedlineCitation']
            article_data = medline['Article']
            
            # PMID
            info['PMID'] = str(medline.get('PMID', ''))
            
            # 标题
            info['标题'] = article_data.get('ArticleTitle', '')
            
            # 发表年份
            try:
                pub_date = article_data['Journal']['JournalIssue']['PubDate']
                year = pub_date.get('Year', '')
                if not year and 'MedlineDate' in pub_date:
                    year = pub_date['MedlineDate'].split(' ')[0]
                info['发表年份'] = year
            except:
                info['发表年份'] = "N/A"
            
            # 研究类型
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
                info['研究类型'] = r_type
            except:
                info['研究类型'] = "N/A"
            
            # 摘要文本
            abstract_text = ""
            if 'Abstract' in article_data and 'AbstractText' in article_data['Abstract']:
                abs_content = article_data['Abstract']['AbstractText']
                if isinstance(abs_content, list):
                    abstract_text = " ".join([str(item) for item in abs_content])
                else:
                    abstract_text = str(abs_content)
            info['摘要文本'] = abstract_text
            
        except Exception as e:
            logger.error(f"提取文献基本信息时出错: {e}")
            info = {
                'PMID': 'N/A',
                '标题': 'N/A', 
                '发表年份': 'N/A',
                '研究类型': 'N/A',
                '摘要文本': ''
            }
        
        return info

# 便捷函数（保持向后兼容）
def search_pubmed(query: str, max_results: int = 20) -> List[str]:
    """
    在PubMed中搜索并返回ID列表（向后兼容函数）
    
    Args:
        query: 搜索查询词
        max_results: 最大结果数
        
    Returns:
        PubMed ID列表
    """
    scraper = PubMedScraper()
    return scraper.search(query, max_results)

def fetch_details(id_list: List[str]) -> List[Dict[str, Any]]:
    """
    根据ID获取文献详细信息（向后兼容函数）
    
    Args:
        id_list: PubMed ID列表
        
    Returns:
        文献详细信息列表
    """
    scraper = PubMedScraper()
    return scraper.fetch_details(id_list)

# 创建全局实例
scraper = PubMedScraper()