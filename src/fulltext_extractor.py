"""
全文提取模块 - 负责从PubMed和免费全文链接中提取文章内容
"""
import requests
import logging
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from src.config import ConfigManager

logger = logging.getLogger(__name__)


class FullTextExtractor:
    """全文内容提取器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化全文提取器"""
        self.config = config_manager or ConfigManager()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.timeout = 20
    
    def check_full_text_availability(self, pmid: str) -> Dict[str, Any]:
        """
        检查PMID对应的文章是否提供免费全文
        
        Args:
            pmid: PubMed ID
        
        Returns:
            包含免费状态和链接信息的字典
        """
        try:
            # 构建PubMed页面URL
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            print(f"🔍 正在检查: {pubmed_url}")
            
            # 获取页面内容
            response = requests.get(pubmed_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 优先级1：直接查找PMC免费全文链接 - 改进版本
            pmc_free_link = None
            
            # 方法1：直接查找title="Free full text at PubMed Central"的a元素
            pmc_free_link = soup.find('a', title="Free full text at PubMed Central")
            
            # 方法2：查找包含PMC和free相关的a元素
            if not pmc_free_link:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    title_attr = link.get('title', '')
                    class_attr = link.get('class', [])
                    text = link.get_text(strip=True)
                    
                    # 将class属性转换为字符串
                    if isinstance(class_attr, list):
                        class_str = ' '.join(class_attr).lower()
                    else:
                        class_str = str(class_attr).lower()
                    
                    # 检查各种免费PMC标识
                    is_pmc_free = False
                    reason = ""
                    
                    # 检查href中的PMC标识
                    if 'pmc' in href.lower() and 'pmc' in class_str:
                        is_pmc_free = True
                        reason = "PMC URL + PMC class"
                    elif 'pmc' in href.lower() and ('free' in title_attr.lower() or 'free' in text.lower()):
                        is_pmc_free = True
                        reason = "PMC URL + Free indicator"
                    elif 'pmc' in class_str and ('free' in title_attr.lower() or 'free' in text.lower()):
                        is_pmc_free = True
                        reason = "PMC class + Free indicator"
                    elif 'pmc' in href.lower() and any(keyword in text.lower() for keyword in ['free', 'pmc article']):
                        is_pmc_free = True
                        reason = "PMC URL + PMC text"
                    
                    if is_pmc_free:
                        pmc_free_link = link
                        print(f"✅ 找到PMC免费全文链接: {reason}")
                        break
            
            if pmc_free_link:
                href = pmc_free_link.get('href', '')
                if href:
                    full_url = href if href.startswith('http') else f"https://pubmed.ncbi.nlm.nih.gov{href}"
                    print(f"✅ 找到PMC免费全文链接: {full_url}")
                    
                    # 获取更多标识信息
                    title_attr = pmc_free_link.get('title', '')
                    class_attr = pmc_free_link.get('class', [])
                    text = pmc_free_link.get_text(strip=True)
                    
                    return {
                        "is_free": True,
                        "pmid": pmid,
                        "pubmed_url": pubmed_url,
                        "links": [{
                            "url": full_url,
                            "title": text or title_attr or "Free PMC article",
                            "is_free": True,
                            "element_found": "improved detection"
                        }],
                        "message": "找到PMC免费全文",
                        "source": "enhanced_pmc_detection"
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
                
                # 检查各种免费指标 - 改进版本
                class_attr = link.get('class', [])
                if isinstance(class_attr, list):
                    class_str = ' '.join(class_attr).lower()
                else:
                    class_str = str(class_attr).lower()
                
                # 检查href中的免费标识
                if 'pmc' in href.lower() or 'pmc.ncbi.nlm.nih.gov' in href.lower():
                    is_free = True
                    free_indicators.append('PMC URL')
                if 'europepmc' in href.lower():
                    is_free = True
                    free_indicators.append('EuropePMC URL')
                if 'pubmedcentral' in href.lower():
                    is_free = True
                    free_indicators.append('PubMed Central')
                
                # 检查class属性中的免费标识
                if 'pmc' in class_str:
                    is_free = True
                    free_indicators.append('PMC class')
                if 'free' in class_str:
                    is_free = True
                    free_indicators.append('Free class')
                
                # 检查title属性
                if title_attr and 'free' in title_attr.lower():
                    is_free = True
                    free_indicators.append('Free title')
                
                # 检查文本内容 - 改进版本
                if text:
                    text_lower = text.lower()
                    if any(keyword in text_lower for keyword in ['free pmc', 'pmc article', 'free full text', 'free article']):
                        is_free = True
                        free_indicators.append('Free PMC text')
                    elif 'free' in text_lower:
                        is_free = True
                        free_indicators.append('Free text')
                    elif 'pmc' in text_lower and 'article' in text_lower:
                        is_free = True
                        free_indicators.append('PMC article text')
                
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
    
    def extract_full_text_content(self, pmid: str, link_url: str = None) -> Dict[str, Any]:
        """
        从免费全文链接提取文章内容
        
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
                availability = self.check_full_text_availability(pmid)
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
            
            # 获取全文页面
            response = requests.get(link_url, headers=self.headers, timeout=self.timeout)
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
    
    def analyze_pmid_with_full_text(self, pmid: str) -> Dict[str, Any]:
        """
        综合分析PMID：检查免费状态并提取全文内容
        
        Args:
            pmid: PubMed ID
        
        Returns:
            完整的分析结果
        """
        print(f"\n🔍 开始分析PMID: {pmid}")
        print("=" * 60)
        
        # 步骤1：检查全文可用性
        print("步骤1: 检查全文可用性...")
        availability = self.check_full_text_availability(pmid)
        
        # 初始化结果
        result = {
            "pmid": pmid,
            "timestamp": self.config.get_current_time(),
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
            full_text = self.extract_full_text_content(pmid)
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


# 创建全局全文提取器实例
full_text_extractor = FullTextExtractor()


# 向后兼容的便捷函数
def check_full_text_availability(pmid: str) -> Dict[str, Any]:
    """检查免费全文可用性（保持向后兼容）"""
    return full_text_extractor.check_full_text_availability(pmid)


def extract_full_text_content(pmid: str, link_url: str = None) -> Dict[str, Any]:
    """提取全文内容（保持向后兼容）"""
    return full_text_extractor.extract_full_text_content(pmid, link_url)


def analyze_pmid_with_full_text(pmid: str) -> Dict[str, Any]:
    """综合分析PMID（保持向后兼容）"""
    return full_text_extractor.analyze_pmid_with_full_text(pmid)