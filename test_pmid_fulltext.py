#!/usr/bin/env python3
"""
测试PMID全文提取功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pubmed import analyze_pmid_with_full_text

def test_pmid_analysis():
    """
    测试PMID分析功能
    """
    # 测试用的PMID列表（一些可能有免费全文的文章）
    test_pmids = [
        "PMC10000000",  # PMC格式的测试ID
        "32542345",     # 真实的PMID，假设有免费全文
        "30000000",     # 另一个测试PMID
    ]
    
    print("=" * 80)
    print("PMID全文提取功能测试")
    print("=" * 80)
    
    for pmid in test_pmids:
        print(f"\n🔍 测试PMID: {pmid}")
        print("-" * 60)
        
        try:
            result = analyze_pmid_with_full_text(pmid)
            
            # 显示基本信息
            print(f"PMID: {result['pmid']}")
            print(f"时间戳: {result['timestamp']}")
            
            # 显示全文检查结果
            ft_check = result['full_text_check']
            print(f"\n📄 全文可用性检查:")
            print(f"  - 是否免费: {'✅ 是' if ft_check['is_free'] else '❌ 否'}")
            print(f"  - 状态信息: {ft_check['message']}")
            
            if 'error' in ft_check:
                print(f"  - 错误信息: {ft_check['error']}")
            
            if ft_check.get('links'):
                print(f"  - 找到 {len(ft_check['links'])} 个链接:")
                for i, link in enumerate(ft_check['links'], 1):
                    print(f"    {i}. {link['title']} ({'免费' if link['is_free'] else '付费'})")
                    print(f"       URL: {link['url']}")
            
            # 如果有免费全文，显示提取结果
            if ft_check['is_free'] and 'full_text_extraction' in result:
                ft_extraction = result['full_text_extraction']
                print(f"\n📖 全文内容提取:")
                print(f"  - 提取成功: {'✅ 是' if ft_extraction.get('extraction_success', False) else '❌ 否'}")
                print(f"  - 信息: {ft_extraction.get('message', 'N/A')}")
                
                if ft_extraction.get('extraction_success'):
                    content = ft_extraction.get('content', {})
                    print(f"  - 标题: {content.get('title', 'N/A')[:100]}...")
                    if 'abstract' in content:
                        print(f"  - 摘要: {len(content['abstract'])} 字符")
                    if 'body_text' in content:
                        print(f"  - 正文: {len(content['body_text'])} 字符")
                    if 'keywords' in content:
                        print(f"  - 关键词: {content['keywords'][:100]}...")
                else:
                    if 'error' in ft_extraction:
                        print(f"  - 错误: {ft_extraction['error']}")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
        
        print("\n" + "=" * 60)
    
    print("\n测试完成!")

def interactive_test():
    """
    交互式测试：让用户输入PMID进行测试
    """
    print("\n" + "=" * 80)
    print("交互式PMID分析")
    print("=" * 80)
    print("请输入PMID进行分析（输入'quit'退出）:")
    
    while True:
        pmid = input("\nPMID: ").strip()
        
        if pmid.lower() in ['quit', 'exit', 'q', '退出']:
            print("退出交互测试")
            break
        
        if not pmid:
            continue
        
        try:
            result = analyze_pmid_with_full_text(pmid)
            
            # 显示结果
            print(f"\n分析结果:")
            print(f"PMID: {result['pmid']}")
            print(f"免费全文: {'✅ 是' if result['full_text_check']['is_free'] else '❌ 否'}")
            
            if result['full_text_check']['is_free']:
                content = result.get('full_text_extraction', {})
                if content.get('extraction_success'):
                    title = content.get('content', {}).get('title', 'N/A')
                    print(f"标题: {title[:100]}...")
                else:
                    print(f"提取失败: {content.get('message', '未知错误')}")
            else:
                print(f"原因: {result['full_text_check']['message']}")
                
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        test_pmid_analysis()