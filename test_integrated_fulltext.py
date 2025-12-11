#!/usr/bin/env python3
"""
测试集成的全文提取功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pubmed import ENABLE_FULLTEXT_EXTRACTION, analyze_pmid_with_full_text, parse_record
import pandas as pd

def test_integrated_functionality():
    """
    测试集成后的全文提取功能
    """
    print("=" * 60)
    print("测试集成全文提取功能")
    print("=" * 60)
    
    # 测试PMID列表（包含已知有免费全文的）
    test_pmids = [
        "37471719",  # 测试PMID
        "36200000",  # 测试PMID  
        "32542345"   # 无免费全文的PMID
    ]
    
    print(f"当前全文提取功能状态: {'启用' if ENABLE_FULLTEXT_EXTRACTION else '禁用'}")
    
    # 手动启用全文提取功能进行测试
    import pubmed
    pubmed.ENABLE_FULLTEXT_EXTRACTION = True
    print(f"测试时全文提取功能状态: {'启用' if pubmed.ENABLE_FULLTEXT_EXTRACTION else '禁用'}")
    
    # 模拟parse_record函数的部分功能测试
    for pmid in test_pmids:
        print(f"\n测试PMID: {pmid}")
        print("-" * 30)
        
        try:
            # 测试全文分析功能
            fulltext_analysis = analyze_pmid_with_full_text(pmid)
            
            # 显示分析结果
            print(f"免费全文状态: {fulltext_analysis.get('is_free', False)}")
            print(f"链接数量: {len(fulltext_analysis.get('links', []))}")
            print(f"提取状态: {fulltext_analysis.get('extraction_success', False)}")
            print(f"消息: {fulltext_analysis.get('message', '无消息')}")
            
            if fulltext_analysis.get('extracted_content'):
                content = fulltext_analysis.get('extracted_content', {})
                print(f"提取的标题: {content.get('title', 'N/A')[:50]}...")
                print(f"提取的摘要: {content.get('abstract', 'N/A')[:100]}...")
            
        except Exception as e:
            print(f"处理PMID {pmid}时出错: {e}")
        
        print()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_integrated_functionality()