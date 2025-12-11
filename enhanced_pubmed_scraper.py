#!/usr/bin/env python3
"""
增强版PubMed访问模块
解决403 Forbidden错误问题，提供多种免费内容判定方法
"""

import requests
import time
import random
import json
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Optional, Tuple


class RateLimiter:
    """请求频率控制器"""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self) -> None:
        """等待随机延迟时间"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 随机延迟1-3秒
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            print(f"⏳ 等待 {sleep_time:.1f} 秒后继续...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class PubMedSession:
    """PubMed会话管理器"""
    
    @staticmethod
    def get_enhanced_headers() -> Dict[str, str]:
        """获取增强的HTTP请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://pubmed.ncbi.nlm.nih.gov/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
    
    def __init__(self):
        self.session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认headers
        self.session.headers.update(self.get_enhanced_headers())
        
        # 初始化会话
        self._initialize_session()
    
    def _initialize_session(self) -> None:
        """初始化PubMed会话"""
        # 跳过会话初始化，直接使用增强headers
        print("🔄 跳过会话初始化，直接使用增强headers")
        self.session.headers.update(self.get_enhanced_headers())
    
    def get_with_retry(self, url: str, **kwargs) -> Optional[requests.Response]:
        """带重试的GET请求"""
        rate_limiter = RateLimiter()
        rate_limiter.wait()
        
        try:
            response = self.session.get(url, **kwargs)
            if response.status_code == 403:
                print(f"❌ 403错误: {url}")
                print("💡 可能需要: 1) 更换IP 2) 等待一段时间 3) 使用代理")
                return None
            return response
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None


class EnhancedPubMedScraper:
    """增强版PubMed内容抓取器"""
    
    def __init__(self):
        self.session = PubMedSession()
        self.rate_limiter = RateLimiter()
    
    def check_fulltext_via_web_scraping(self, pmid: str) -> Dict[str, any]:
        """通过增强的网页抓取检查免费全文"""
        try:
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            print(f"🔍 正在检查: {pubmed_url}")
            
            response = self.session.get_with_retry(pubmed_url, timeout=15)
            if not response:
                return {
                    'is_free': False,
                    'pmid': pmid,
                    'source': 'web_scraping',
                    'error': '无法获取页面内容',
                    'confidence': 'low'
                }
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 优先级1：直接查找PMC免费标识
            pmc_free_link = soup.find('a', title="Free full text at PubMed Central")
            if pmc_free_link:
                href = pmc_free_link.get('href', '')
                if href:
                    full_url = href if href.startswith('http') else f"https://pubmed.ncbi.nlm.nih.gov{href}"
                    return {
                        "is_free": True,
                        "pmid": pmid,
                        "source": "web_scraping",
                        "confidence": "high",
                        "links": [{
                            "url": full_url,
                            "title": "Free full text at PubMed Central",
                            "type": "pmc_direct"
                        }],
                        "message": "找到PMC免费全文标识"
                    }
            
            # 优先级2：查找全文链接区域
            full_text_section = soup.find('div', {'data-content-id': 'full-text-links'})
            if not full_text_section:
                full_text_section = soup.find('div', class_='full-text-links')
            
            free_links = []
            if full_text_section:
                link_elements = full_text_section.find_all('a', href=True)
                
                for link in link_elements:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    title_attr = link.get('title', '')
                    
                    is_free = False
                    free_indicators = []
                    
                    # 检查免费指标
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
                    
                    if is_free:
                        link_info = {
                            "url": href if href.startswith('http') else f"https://pubmed.ncbi.nlm.nih.gov{href}",
                            "title": text,
                            "indicators": free_indicators
                        }
                        free_links.append(link_info)
            
            if free_links:
                return {
                    'is_free': True,
                    'pmid': pmid,
                    'source': 'web_scraping',
                    'confidence': 'medium',
                    'links': free_links,
                    'message': f"通过网页分析找到 {len(free_links)} 个免费链接"
                }
            else:
                return {
                    'is_free': False,
                    'pmid': pmid,
                    'source': 'web_scraping',
                    'confidence': 'medium',
                    'message': '未找到免费全文链接'
                }
        
        except Exception as e:
            return {
                'is_free': False,
                'pmid': pmid,
                'source': 'web_scraping',
                'error': str(e),
                'message': '网页抓取失败'
            }
    
    def check_fulltext_via_europepmc(self, pmid: str) -> Dict[str, any]:
        """通过EuropePMC API检查免费全文"""
        try:
            print(f"🌍 通过EuropePMC检查PMID: {pmid}")
            
            # EuropePMC API endpoint
            api_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            params = {
                'query': f'EXT_ID:{pmid}',
                'resultType': 'core',
                'format': 'json'
            }
            
            self.rate_limiter.wait()
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('resultList', {}).get('result'):
                result = data['resultList']['result'][0]
                # 修复检测逻辑：检查是否有fullTextIdList
                is_free = bool(result.get('fullTextIdList', {}).get('fullTextId'))
                
                return {
                    'is_free': is_free,
                    'pmid': pmid,
                    'source': 'europepmc_api',
                    'confidence': 'high' if is_free else 'medium',
                    'pmcid': result.get('pmcid'),
                    'doi': result.get('doi'),
                    'title': result.get('title'),
                    'fullTextIdList': result.get('fullTextIdList'),
                    'message': 'EuropePMC检查完成'
                }
            else:
                return {
                    'is_free': False,
                    'pmid': pmid,
                    'source': 'europepmc_api',
                    'confidence': 'low',
                    'message': 'EuropePMC未找到相关记录'
                }
        
        except Exception as e:
            return {
                'is_free': False,
                'pmid': pmid,
                'source': 'europepmc_api',
                'error': str(e),
                'message': 'EuropePMC API访问失败'
            }
    
    def check_fulltext_via_ncbi_api(self, pmid: str) -> Dict[str, any]:
        """通过NCBI E-utilities API检查免费全文"""
        try:
            print(f"🧬 通过NCBI API检查PMID: {pmid}")
            
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
            
            # 直接使用PMID作为ID查询
            summary_url = f"{base_url}esummary.fcgi"
            summary_params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'json'
            }
            
            self.rate_limiter.wait()
            summary_response = requests.get(summary_url, params=summary_params, timeout=10)
            summary_data = summary_response.json()
            
            # 检查是否找到记录
            if not summary_data.get('result', {}).get(pmid):
                return {
                    'is_free': False,
                    'pmid': pmid,
                    'source': 'ncbi_api',
                    'confidence': 'low',
                    'message': 'NCBI未找到相关记录'
                }
            
            article_data = summary_data['result'][pmid]
            
            # 检查PMC状态 - 从articleids数组中查找
            pmcid_found = None
            for article_id in article_data.get('articleids', []):
                if article_id.get('idtype') == 'pmc':
                    pmcid_found = article_id.get('value')
                    break
            
            has_free = bool(pmcid_found)
            
            return {
                'is_free': has_free,
                'pmid': pmid,
                'source': 'ncbi_api',
                'confidence': 'high' if has_free else 'medium',
                'pmcid': pmcid_found,
                'message': 'NCBI API检查完成'
            }
        
        except Exception as e:
            return {
                'is_free': False,
                'pmid': pmid,
                'source': 'ncbi_api',
                'error': str(e),
                'message': 'NCBI API访问失败'
            }
    
    def check_fulltext_comprehensive(self, pmid: str) -> Dict[str, any]:
        """综合多种方法检查免费全文"""
        print(f"\n🔍 开始综合检查PMID: {pmid}")
        print("=" * 50)
        
        results = []
        
        # 方法1: EuropePMC API (最快，最可靠)
        print("\n📡 方法1: EuropePMC API")
        result1 = self.check_fulltext_via_europepmc(pmid)
        results.append(result1)
        print(f"结果: {result1['message']} - 免费: {result1['is_free']}")
        
        # 方法2: NCBI API
        print("\n🧬 方法2: NCBI E-utilities API")
        result2 = self.check_fulltext_via_ncbi_api(pmid)
        results.append(result2)
        print(f"结果: {result2['message']} - 免费: {result2['is_free']}")
        
        # 方法3: 网页抓取 (作为最后手段)
        print("\n🕷️ 方法3: 网页抓取")
        result3 = self.check_fulltext_via_web_scraping(pmid)
        results.append(result3)
        print(f"结果: {result3.get('message', '未知错误')} - 免费: {result3.get('is_free', False)}")
        
        # 综合决策
        print(f"\n📊 综合分析结果")
        print("=" * 50)
        
        # 统计各方法结果
        free_count = sum(1 for r in results if r.get('is_free', False))
        high_confidence_count = sum(1 for r in results if r.get('confidence') == 'high')
        
        # 决策逻辑
        if free_count >= 2:
            final_result = {
                'is_free': True,
                'confidence': 'high',
                'consensus': f'{free_count}/3方法确认免费',
                'source': 'consensus_multi_method'
            }
        elif free_count == 1:
            # 检查是否有高置信度结果
            high_conf_result = next((r for r in results if r.get('is_free') and r.get('confidence') == 'high'), None)
            if high_conf_result:
                final_result = {
                    'is_free': True,
                    'confidence': 'high',
                    'consensus': '高置信度方法确认免费',
                    'source': 'single_high_confidence'
                }
            else:
                final_result = {
                    'is_free': False,
                    'confidence': 'medium',
                    'consensus': '仅1/3方法显示免费，置信度不足',
                    'source': 'consensus_low_confidence'
                }
        else:
            final_result = {
                'is_free': False,
                'confidence': 'high',
                'consensus': '0/3方法确认免费',
                'source': 'consensus_no_free'
            }
        
        # 合并结果
        final_result.update({
            'pmid': pmid,
            'method_results': results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        print(f"🎯 最终决策: 免费={final_result['is_free']}, 置信度={final_result['confidence']}")
        print(f"📈 共识: {final_result['consensus']}")
        
        return final_result


def test_enhanced_scraper():
    """测试增强版抓取器"""
    scraper = EnhancedPubMedScraper()
    
    test_pmids = [
        "30049270",  # 有PMC ID的已知PMID
        "23430950",  # 问题PMID
    ]
    
    for pmid in test_pmids:
        print(f"\n🧪 测试增强版抓取器 - PMID: {pmid}")
        print("=" * 60)
        
        result = scraper.check_fulltext_comprehensive(pmid)
        
        print(f"\n📋 最终结果:")
        print(f"PMID: {result['pmid']}")
        print(f"免费全文: {result['is_free']}")
        print(f"置信度: {result['confidence']}")
        print(f"决策依据: {result['consensus']}")
        print(f"数据源: {result['source']}")
        
        # 保存详细结果到文件
        filename = f"enhanced_result_{pmid}_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 详细结果已保存到: {filename}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    test_enhanced_scraper()