#!/usr/bin/env python3
"""
PMID分析器 - 检查文章是否免费并获取全文
"""

import requests
import re
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Tuple
import time

logger = logging.getLogger(__name__)

def check_full_text_availability(pmid: str) -> Dict[str, any]:
    """
    检查PMID对应的文章是否有免费全文
    
    Args:
        pmid: PubMed ID
        
    Returns:
        包含以下字段的字典：
        - is_free: bool，是否免费
        - full_text_url: str，免费全文链接
        - pdf_url: str，PDF下载链接（如果有）
        - source: str，来源网站
        - message: str，状态信息
    """
    pubmed_url = f"http://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    
    try:
        # 获取PubMed页面
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(pubmed_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 检查免费全文链接
        full_text_links = soup.find_all('a', href=re.compile(r'(full|text|pdf)', re.I))
        free_text_links = soup.find_all('a', string=re.compile(r'(Free|Full\s+text|PDF)', re.I))
        
        is_free = False
        full_text_url = ""
        pdf_url = ""
        source = ""
        message = ""
        
        # 检查PMC (PubMed Central) 是否有免费全文
        pmc_link = soup.find('a', href=re.compile(r'ncbi\.nlm\.nih\.gov/pmc', re.I))
        if pmc_link:
            pmc_url = pmc_link.get('href', '')
            if pmc_url.startswith('/'):
                pmc_url = "https://www.ncbi.nlm.nih.gov" + pmc_url
            
            is_free = True
            full_text_url = pmc_url
            source = "PMC (PubMed Central)"
            message = "在PMC中找到免费全文"
        
        # 检查其他免费全文来源
        else:
            for link in free_text_links + full_text_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                # 检查是否是免费全文
                if any(keyword in href.lower() for keyword in ['free', 'full', 'pdf']):
                    if href.startswith('http'):
                        full_text_url = href
                    else:
                        full_text_url = "http://pubmed.ncbi.nlm.nih.gov" + href
                    
                    # 确定来源
                    if 'europepmc' in href.lower():
                        source = "Europe PMC"
                    elif 'sci-hub' in href.lower():
                        source = "Sci-Hub (注意版权)"
                    elif 'nih.gov' in href.lower():
                        source = "NIH/NCBI"
                    else:
                        source = "其他来源"
                    
                    is_free = True
                    message = f"找到免费全文链接: {source}"
                    break
        
        if not is_free:
            message = "未找到免费全文"
        
        return {
            'is_free': is_free,
            'full_text_url': full_text_url,
            'pdf_url': pdf_url,
            'source': source,
            'message': message,
            'pubmed_url': pubmed_url
        }
        
    except Exception as e:
        logger.error(f"检查PMID {pmid} 的免费全文时出错: {e}")
        return {
            'is_free': False,
            'full_text_url': '',
            'pdf_url': '',
            'source': '',
            'message': f'检查失败: {str(e)}',
            'pubmed_url': pubmed_url
        }

def extract_full_text_content(full_text_url: str, source: str) -> Dict[str, any]:
    """
    从全文URL提取内容
    
    Args:
        full_text_url: 全文URL
        source: 来源网站
        
    Returns:
        包含提取内容的字典
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(full_text_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        if source == "PMC (PubMed Central)":
            return extract_pmc_content(response.content)
        elif "europepmc" in source.lower():
            return extract_europepmc_content(response.content)
        else:
            return extract_generic_content(response.content)
            
    except Exception as e:
        logger.error(f"提取全文内容时出错: {e}")
        return {
            'content': '',
            'sections': {},
            'message': f'提取失败: {str(e)}'
        }

def extract_pmc_content(html_content: bytes) -> Dict[str, any]:
    """从PMC页面提取内容"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    content = {
        'content': '',
        'sections': {},
        'message': 'PMC内容提取成功'
    }
    
    # 提取标题
    title = soup.find('h1')
    if title:
        content['title'] = title.get_text().strip()
    
    # 提取摘要
    abstract = soup.find('div', class_='t-content') or soup.find('section', class_='abstract')
    if abstract:
        content['abstract'] = abstract.get_text().strip()
    
    # 提取方法
    methods = soup.find('div', string=re.compile(r'Methods?|Methodology', re.I))
    if methods:
        content['methods'] = methods.get_text().strip()
    
    # 提取结果
    results = soup.find('div', string=re.compile(r'Results?', re.I))
    if results:
        content['results'] = results.get_text().strip()
    
    # 提取结论
    conclusion = soup.find('div', string=re.compile(r'Conclusion|Discussion', re.I))
    if conclusion:
        content['conclusion'] = conclusion.get_text().strip()
    
    # 合并所有文本内容
    all_text = ""
    for key, value in content.items():
        if key != 'message' and value:
            all_text += f"\n{key.upper()}:\n{value}\n"
    
    content['content'] = all_text.strip()
    
    return content

def extract_europepmc_content(html_content: bytes) -> Dict[str, any]:
    """从Europe PMC页面提取内容"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    content = {
        'content': '',
        'sections': {},
        'message': 'Europe PMC内容提取成功'
    }
    
    # 提取主要内容区域
    main_content = soup.find('div', class_='article-content') or soup.find('main')
    if main_content:
        content['content'] = main_content.get_text().strip()
    else:
        content['content'] = soup.get_text().strip()
    
    return content

def extract_generic_content(html_content: bytes) -> Dict[str, any]:
    """通用的内容提取方法"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除脚本和样式元素
    for script in soup(["script", "style"]):
        script.decompose()
    
    content = {
        'content': soup.get_text().strip(),
        'sections': {},
        'message': '通用内容提取成功'
    }
    
    return content

def analyze_pmid_comprehensive(pmid: str) -> Dict[str, any]:
    """
    综合分析PMID，包括检查免费状态和提取内容
    
    Args:
        pmid: PubMed ID
        
    Returns:
        完整的分析结果
    """
    logger.info(f"开始分析PMID: {pmid}")
    
    # 第一步：检查免费全文状态
    free_check = check_full_text_availability(pmid)
    logger.info(f"免费状态检查结果: {free_check['message']}")
    
    result = {
        'pmid': pmid,
        'free_check': free_check,
        'full_text_content': None,
        'enhanced_extraction': None
    }
    
    # 第二步：如果有免费全文，尝试获取内容
    if free_check['is_free'] and free_check['full_text_url']:
        logger.info("开始提取全文内容...")
        
        full_text_content = extract_full_text_content(
            free_check['full_text_url'], 
            free_check['source']
        )
        result['full_text_content'] = full_text_content
        
        logger.info(f"全文提取结果: {full_text_content['message']}")
        
        # 第三步：如果成功获取全文，使用全文内容进行更详细的信息提取
        if full_text_content['content']:
            logger.info("使用全文内容进行增强信息提取...")
            
            # 这里可以调用您现有的AI提取函数，但传入全文内容
            try:
                # 导入现有的提取函数
                import sys
                sys.path.append('/Users/x/Downloads/fuEvidenceExcel')
                from pubmed import extract_info_with_ai
                
                # 使用全文内容进行提取
                enhanced_extraction = extract_info_with_ai(full_text_content['content'])
                result['enhanced_extraction'] = enhanced_extraction
                
                logger.info("增强信息提取完成")
                
            except Exception as e:
                logger.error(f"增强信息提取失败: {e}")
                result['enhanced_extraction'] = {'error': str(e)}
    
    return result

# 测试函数
def test_pmid_analysis():
    """测试PMID分析功能"""
    test_pmids = ["38476934", "38412345"]  # 可以替换为实际的PMID
    
    for pmid in test_pmids:
        print(f"\n=== 分析PMID: {pmid} ===")
        result = analyze_pmid_comprehensive(pmid)
        
        print(f"PMID: {result['pmid']}")
        print(f"免费状态: {result['free_check']['is_free']}")
        print(f"来源: {result['free_check']['source']}")
        print(f"消息: {result['free_check']['message']}")
        
        if result['full_text_content']:
            print(f"全文提取: {result['full_text_content']['message']}")
            
        if result['enhanced_extraction']:
            print("增强提取结果:")
            for key, value in result['enhanced_extraction'].items():
                print(f"  {key}: {value}")
        
        time.sleep(2)  # 避免请求过于频繁

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_pmid_analysis()