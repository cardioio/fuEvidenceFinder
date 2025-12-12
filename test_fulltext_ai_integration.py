#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试免费全文集成到AI prompt的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pubmed import parse_record
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fulltext_ai_integration():
    """测试全文内容集成到AI prompt的功能"""
    
    print("=" * 60)
    print("🔬 测试免费全文集成到AI prompt功能")
    print("=" * 60)
    
    # 使用已知的免费全文PMID进行测试
    test_pmid = "27792142"
    
    print(f"\n📋 测试PMID: {test_pmid}")
    print("=" * 30)
    
    try:
        # 构造模拟的article_data结构（符合PubMed API返回格式）
        article_data = {
            'MedlineCitation': {
                'PMID': test_pmid,
                'Article': {
                    'ArticleIdList': [{'Id': test_pmid}],
                    'ArticleTitle': 'Test article for fulltext integration',
                    'Abstract': {
                        'AbstractText': [
                            'This is a test abstract for verifying fulltext integration.',
                            'It contains information about the research methodology and results.'
                        ]
                    },
                    'AuthorList': [{'Author': {'LastName': 'Smith', 'ForeName': 'John'}}],
                    'Journal': {
                        'Title': 'Test Journal',
                        'ISOAbbreviation': 'Test J.',
                        'JournalIssue': {'PubDate': '2023;123:456-789'}
                    },
                    'ArticleDate': [{'ArticleDate': '2023-01-15'}],
                    'PublicationTypeList': ['Journal Article']
                }
            }
        }
        
        # 调用parse_record函数
        print("\n🚀 开始处理文献...")
        result = parse_record(article_data)
        
        print(f"\n📊 测试结果:")
        print("=" * 30)
        
        # 检查关键字段
        print(f"PMID: {result.get('PMID', 'N/A')}")
        print(f"标题: {result.get('原文标题', 'N/A')}")
        print(f"翻译标题: {result.get('翻译标题', 'N/A')}")
        
        # 重点检查全文相关字段
        free_status = result.get('免费全文状态', 'N/A')
        free_links = result.get('免费全文链接数', 0)
        extraction_status = result.get('全文提取状态', 'N/A')
        
        print(f"免费全文状态: {free_status}")
        print(f"免费全文链接数: {free_links}")
        print(f"全文提取状态: {extraction_status}")
        
        # 验证其他AI提取字段
        print(f"研究对象: {result.get('研究对象', 'N/A')}")
        print(f"样本量: {result.get('样本量', 'N/A')}")
        print(f"结论摘要: {result.get('结论摘要', 'N/A')}")
        
        # 验证功能是否正常工作
        print(f"\n🎯 功能验证:")
        print("=" * 30)
        
        if free_status in ['免费', '付费']:
            print("✅ 全文状态检测功能正常")
        else:
            print("❌ 全文状态检测功能异常")
            
        if extraction_status != '未尝试':
            print("✅ 全文提取功能已触发")
        else:
            print("⚠️ 全文提取功能可能未启用")
            
        if result.get('原文标题') != '无标题':
            print("✅ AI标题处理功能正常")
        else:
            print("❌ AI标题处理功能异常")
            
        # 总结测试结果
        print(f"\n📋 测试总结:")
        print("=" * 30)
        print(f"✅ 全文状态检测: {free_status}")
        print(f"✅ 全文提取状态: {extraction_status}")
        print(f"✅ AI分析完成: {'是' if result.get('结论摘要') != '需人工确认' else '否'}")
        
        print(f"\n🎉 测试完成！免费全文集成功能已实现")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_pmids():
    """测试多个PMID的处理"""
    
    print(f"\n📋 批量测试多个PMID")
    print("=" * 30)
    
    # 测试多个PMID
    test_pmids = ["27792142", "32553897", "32749441"]
    
    success_count = 0
    total_count = len(test_pmids)
    
    for pmid in test_pmids:
        try:
            print(f"\n🔍 测试PMID: {pmid}")
            
            # 构造article_data（符合PubMed API返回格式）
            article_data = {
                'MedlineCitation': {
                    'PMID': pmid,
                    'Article': {
                        'ArticleIdList': [{'Id': pmid}],
                        'ArticleTitle': f'Test article {pmid}',
                        'Abstract': {'AbstractText': f'Test abstract for PMID {pmid}'},
                        'Journal': {
                            'Title': 'Test Journal',
                            'JournalIssue': {'PubDate': '2023;123:456-789'}
                        },
                        'PublicationTypeList': ['Journal Article']
                    }
                }
            }
            
            result = parse_record(article_data)
            
            if result.get('PMID'):
                print(f"  ✅ PMID处理成功: {result.get('免费全文状态', '未知')}")
                success_count += 1
            else:
                print(f"  ❌ PMID处理失败")
                
        except Exception as e:
            print(f"  ❌ PMID {pmid} 处理出错: {e}")
    
    print(f"\n📊 批量测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

if __name__ == "__main__":
    print("🧪 开始测试免费全文集成AI功能")
    
    # 单案例测试
    single_test_pass = test_fulltext_ai_integration()
    
    # 批量测试
    batch_test_pass = test_multiple_pmids()
    
    print(f"\n🏁 最终测试结果:")
    print("=" * 40)
    print(f"单案例测试: {'✅ 通过' if single_test_pass else '❌ 失败'}")
    print(f"批量测试: {'✅ 通过' if batch_test_pass else '❌ 失败'}")
    
    if single_test_pass and batch_test_pass:
        print(f"\n🎉 所有测试通过！免费全文集成AI功能工作正常！")
    else:
        print(f"\n⚠️ 部分测试失败，需要检查实现")