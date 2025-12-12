"""
主程序入口模块 - 提供命令行界面和程序入口点
"""
import argparse
import logging
import sys
import time
from typing import Dict, Any, Optional
import os

# 导入配置和工具模块
from src.config import ConfigManager
from src.pubmed_scraper import search_pubmed, fetch_details, PubMedScraper
from src.data_parser import extract_info_with_regex, parse_record, DataParser
from src.ai_extractor import extract_info_with_ai, AIExtractor
from src.fulltext_extractor import check_full_text_availability, extract_full_text_content, analyze_pmid_with_full_text
from src.api_key_manager import APIKeyPoolManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MainApplication:
    """主应用程序类"""
    
    def __init__(self):
        """初始化主应用程序"""
        self.config = ConfigManager()
        self.logger = logging.getLogger(__name__)
        
    def run_search_mode(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        运行搜索模式
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            搜索结果字典
        """
        print(f"🔍 启动搜索模式")
        print(f"查询: {query}")
        print(f"最大结果数: {max_results}")
        print("=" * 60)
        
        try:
            # 使用PubMed搜索器
            results = search_pubmed(query, max_results=max_results)
            
            print(f"✅ 搜索完成，找到 {len(results)} 条结果")
            return {
                "success": True,
                "query": query,
                "max_results": max_results,
                "found_results": len(results),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": []
            }
    
    def run_extraction_mode(self, pmid: str, extraction_type: str = "auto") -> Dict[str, Any]:
        """
        运行提取模式
        
        Args:
            pmid: PubMed ID
            extraction_type: 提取类型 ("ai", "regex", "fulltext", "auto")
        
        Returns:
            提取结果字典
        """
        print(f"📄 启动提取模式")
        print(f"PMID: {pmid}")
        print(f"提取类型: {extraction_type}")
        print("=" * 60)
        
        try:
            # 获取PubMed记录
            record = fetch_details(pmid)
            if not record:
                return {
                    "success": False,
                    "pmid": pmid,
                    "error": "无法获取PubMed记录"
                }
            
            print(f"✅ 获取PubMed记录成功")
            
            # 根据提取类型选择提取方法
            if extraction_type == "regex" or extraction_type == "auto":
                # 尝试正则表达式提取
                abstract = record.get('abstract', '')
                if abstract:
                    regex_result = extract_info_with_regex(abstract)
                    print(f"📝 正则提取完成，提取 {len(regex_result)} 个字段")
                else:
                    regex_result = {}
            
            if extraction_type == "ai" or extraction_type == "auto":
                # 尝试AI提取
                abstract = record.get('abstract', '')
                if abstract:
                    ai_result = extract_info_with_ai(abstract)
                    print(f"🤖 AI提取完成，提取 {len(ai_result)} 个字段")
                else:
                    ai_result = {}
            
            if extraction_type == "fulltext":
                # 尝试全文提取
                fulltext_result = analyze_pmid_with_full_text(pmid)
                print(f"📖 全文提取完成，成功: {fulltext_result.get('extraction_success', False)}")
            else:
                fulltext_result = {}
            
            # 合并结果
            final_result = {
                "success": True,
                "pmid": pmid,
                "pubmed_record": record,
                "extraction_results": {
                    "regex": regex_result if extraction_type in ["regex", "auto"] else {},
                    "ai": ai_result if extraction_type in ["ai", "auto"] else {},
                    "fulltext": fulltext_result if extraction_type == "fulltext" else {}
                }
            }
            
            print(f"✅ 提取完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"提取失败: {str(e)}")
            return {
                "success": False,
                "pmid": pmid,
                "error": str(e)
            }
    
    def run_analysis_mode(self, pmids: list, analysis_type: str = "full") -> Dict[str, Any]:
        """
        运行分析模式
        
        Args:
            pmids: PubMed ID列表
            analysis_type: 分析类型 ("quick", "full", "fulltext")
        
        Returns:
            分析结果字典
        """
        print(f"📊 启动分析模式")
        print(f"PMID数量: {len(pmids)}")
        print(f"分析类型: {analysis_type}")
        print("=" * 60)
        
        start_time = time.time()
        results = {
            "success": True,
            "total_pmids": len(pmids),
            "analyzed_pmids": 0,
            "failed_pmids": 0,
            "analysis_results": [],
            "summary_statistics": {},
            "execution_time": 0
        }
        
        for i, pmid in enumerate(pmids, 1):
            print(f"\n🔬 分析 {i}/{len(pmids)}: {pmid}")
            print("-" * 40)
            
            try:
                if analysis_type == "quick":
                    # 快速分析：只获取基本信息
                    record = fetch_details(pmid)
                    if record:
                        result = {
                            "pmid": pmid,
                            "success": True,
                            "title": record.get('title', ''),
                            "authors": record.get('authors', ''),
                            "journal": record.get('journal', ''),
                            "year": record.get('year', ''),
                            "analysis_type": "quick"
                        }
                        results["analyzed_pmids"] += 1
                    else:
                        result = {"pmid": pmid, "success": False, "error": "无法获取记录"}
                        results["failed_pmids"] += 1
                
                elif analysis_type == "full":
                    # 完整分析：基本信息 + AI提取
                    record = fetch_details(pmid)
                    if record:
                        abstract = record.get('abstract', '')
                        ai_extraction = extract_info_with_ai(abstract) if abstract else {}
                        
                        result = {
                            "pmid": pmid,
                            "success": True,
                            "pubmed_record": record,
                            "ai_extraction": ai_extraction,
                            "analysis_type": "full"
                        }
                        results["analyzed_pmids"] += 1
                    else:
                        result = {"pmid": pmid, "success": False, "error": "无法获取记录"}
                        results["failed_pmids"] += 1
                
                elif analysis_type == "fulltext":
                    # 全文分析：全文可用性检查 + 内容提取
                    fulltext_analysis = analyze_pmid_with_full_text(pmid)
                    result = {
                        "pmid": pmid,
                        "success": fulltext_analysis.get("extraction_success", False),
                        "fulltext_analysis": fulltext_analysis,
                        "analysis_type": "fulltext"
                    }
                    if result["success"]:
                        results["analyzed_pmids"] += 1
                    else:
                        results["failed_pmids"] += 1
                
                print(f"✅ 分析完成: {result.get('success', False)}")
                
            except Exception as e:
                print(f"❌ 分析失败: {str(e)}")
                result = {"pmid": pmid, "success": False, "error": str(e)}
                results["failed_pmids"] += 1
            
            results["analysis_results"].append(result)
        
        # 计算统计信息
        end_time = time.time()
        results["execution_time"] = round(end_time - start_time, 3)
        results["success_rate"] = round(
            (results["analyzed_pmids"] / results["total_pmids"]) * 100, 1
        ) if results["total_pmids"] > 0 else 0
        
        # 生成摘要统计
        if analysis_type == "full" and results["analyzed_pmids"] > 0:
            # 分析AI提取结果的统计信息
            ai_results = [
                result.get("ai_extraction", {})
                for result in results["analysis_results"]
                if result.get("success") and result.get("ai_extraction")
            ]
            
            if ai_results:
                study_types = {}
                total_samples = 0
                valid_samples = 0
                
                for extraction in ai_results:
                    study_type = extraction.get("study_type", "Unknown")
                    study_types[study_type] = study_types.get(study_type, 0) + 1
                    
                    sample_size = extraction.get("sample_size")
                    if sample_size:
                        try:
                            if isinstance(sample_size, str):
                                sample_num = int(''.join(filter(str.isdigit, sample_size)))
                            else:
                                sample_num = int(sample_size)
                            total_samples += sample_num
                            valid_samples += 1
                        except:
                            pass
                
                results["summary_statistics"] = {
                    "study_type_distribution": study_types,
                    "average_sample_size": round(total_samples / valid_samples, 1) if valid_samples > 0 else 0,
                    "valid_sample_count": valid_samples
                }
        
        print(f"\n📊 分析完成")
        print(f"总PMID数: {results['total_pmids']}")
        print(f"成功分析: {results['analyzed_pmids']} ({results['success_rate']}%)")
        print(f"失败分析: {results['failed_pmids']}")
        print(f"执行时间: {results['execution_time']}秒")
        print("=" * 60)
        
        return results


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="PubMed文献分析工具 - 支持搜索、提取和分析功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s test --type ai                    # 测试AI提取功能
  %(prog)s search "cancer treatment"         # 搜索文献
  %(prog)s extract 12345678 --type ai        # 提取指定PMID的信息
  %(prog)s analyze 12345678 87654321         # 分析多个PMID
        """
    )
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索PubMed文献')
    search_parser.add_argument('query', help='搜索查询字符串')
    search_parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=10,
        help='最大结果数 (默认: 10)'
    )
    
    # 提取命令
    extract_parser = subparsers.add_parser('extract', help='提取文献信息')
    extract_parser.add_argument('pmid', help='PubMed ID')
    extract_parser.add_argument(
        '--type', '-t',
        choices=['ai', 'regex', 'fulltext', 'auto'],
        default='auto',
        help='提取类型 (默认: auto)'
    )
    
    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析文献')
    analyze_parser.add_argument('pmids', nargs='+', help='一个或多个PubMed ID')
    analyze_parser.add_argument(
        '--type', '-t',
        choices=['quick', 'full', 'fulltext'],
        default='full',
        help='分析类型 (默认: full)'
    )
    
    return parser


def main():
    """主程序入口点"""
    try:
        # 创建参数解析器
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # 如果没有提供命令，显示帮助信息
        if not args.command:
            parser.print_help()
            return
        
        # 创建主应用程序实例
        app = MainApplication()
        
        print(f"🚀 PubMed文献分析工具启动")
        print(f"命令: {args.command}")
        print(f"时间: {app.config.get_current_time()}")
        print("=" * 80)
        
        # 根据命令执行相应功能
        if args.command == 'search':
            result = app.run_search_mode(args.query, args.max_results)
            
        elif args.command == 'extract':
            result = app.run_extraction_mode(args.pmid, args.type)
            
        elif args.command == 'analyze':
            result = app.run_analysis_mode(args.pmids, args.type)
        
        # 输出结果摘要
        print(f"\n📋 执行结果摘要:")
        if 'success' in result:
            print(f"   状态: {'成功' if result['success'] else '失败'}")
        
        if args.command == 'search' and 'found_results' in result:
            print(f"   找到结果: {result['found_results']} 条")
        elif args.command == 'extract' and 'extraction_results' in result:
            extraction_results = result['extraction_results']
            if extraction_results.get('ai'):
                print(f"   AI提取字段数: {len(extraction_results['ai'])}")
            if extraction_results.get('regex'):
                print(f"   正则提取字段数: {len(extraction_results['regex'])}")
        elif args.command == 'analyze':
            print(f"   分析PMID数: {result['total_pmids']}")
            print(f"   成功分析: {result['analyzed_pmids']} ({result['success_rate']}%)")
            print(f"   执行时间: {result['execution_time']}秒")
        
        print("=" * 80)
        print("✅ 程序执行完成")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序执行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序执行出错: {str(e)}")
        logger.error(f"主程序异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()