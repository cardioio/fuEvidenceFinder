#!/usr/bin/env python3
"""
测试改进后的免费全文检测功能
专门针对用户报告的问题案例进行验证
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fulltext_extractor import FullTextExtractor

def test_free_detection_case():
    """测试用户报告的问题案例：PMID 27792142"""
    print("=" * 80)
    print("🔍 测试改进后的免费全文检测功能")
    print("=" * 80)
    
    # 用户报告的问题案例
    test_pmid = "27792142"
    
    print(f"\n📋 测试案例: PMID {test_pmid}")
    print("   预期结果: 应该检测为免费（用户报告有'Free PMC article'链接）")
    
    # 初始化提取器
    extractor = FullTextExtractor()
    
    # 测试免费检测功能
    print(f"\n🔍 开始检测PMID {test_pmid}的免费状态...")
    availability = extractor.check_full_text_availability(test_pmid)
    
    # 分析结果
    print(f"\n📊 检测结果:")
    print(f"   免费状态: {'✅ 是' if availability['is_free'] else '❌ 否'}")
    print(f"   信息来源: {availability.get('source', 'unknown')}")
    print(f"   详细消息: {availability.get('message', '无')}")
    
    if availability.get('links'):
        print(f"\n🔗 发现的链接数量: {len(availability['links'])}")
        for i, link in enumerate(availability['links'], 1):
            print(f"   链接 {i}:")
            print(f"     URL: {link.get('url', 'N/A')[:100]}...")
            print(f"     标题: {link.get('title', 'N/A')}")
            print(f"     是否免费: {'✅ 是' if link.get('is_free') else '❌ 否'}")
            if 'indicators' in link:
                print(f"     检测指标: {', '.join(link['indicators'])}")
            print()
    
    if availability.get('all_links'):
        print(f"\n📝 所有发现的链接:")
        for i, link in enumerate(availability['all_links'][:5], 1):  # 只显示前5个
            print(f"   {i}. {link.get('title', 'N/A')} - {link.get('url', 'N/A')[:80]}...")
            print(f"      免费: {'✅' if link.get('is_free') else '❌'}")
            if 'indicators' in link:
                print(f"      指标: {', '.join(link['indicators'])}")
    
    # 验证结果
    if availability['is_free']:
        print(f"\n✅ 测试通过: 成功检测到PMID {test_pmid}提供免费全文")
        return True
    else:
        print(f"\n❌ 测试失败: 未能检测到PMID {test_pmid}的免费全文")
        print("   可能需要进一步调整检测逻辑")
        return False

def test_multiple_pmids():
    """测试多个不同的PMID"""
    print("\n" + "=" * 80)
    print("🧪 多案例测试")
    print("=" * 80)
    
    # 测试多个PMID（包含已知免费和付费的）
    test_pmids = [
        "27792142",  # 用户报告的问题案例
        "30049270",  # 之前测试过的案例
        "23430950",  # 另一个测试案例
    ]
    
    extractor = FullTextExtractor()
    
    success_count = 0
    total_count = len(test_pmids)
    
    for pmid in test_pmids:
        print(f"\n📋 测试PMID: {pmid}")
        try:
            availability = extractor.check_full_text_availability(pmid)
            print(f"   免费状态: {'✅ 是' if availability['is_free'] else '❌ 否'}")
            print(f"   检测源: {availability.get('source', 'unknown')}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ 测试出错: {str(e)}")
    
    print(f"\n📊 多案例测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

if __name__ == "__main__":
    print("🚀 启动改进后的免费检测功能测试")
    
    # 单案例测试
    single_test_result = test_free_detection_case()
    
    # 多案例测试
    multiple_test_result = test_multiple_pmids()
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)
    print(f"单案例测试 (PMID 27792142): {'✅ 通过' if single_test_result else '❌ 失败'}")
    print(f"多案例测试: {'✅ 通过' if multiple_test_result else '❌ 失败'}")
    
    if single_test_result and multiple_test_result:
        print("\n🎉 所有测试通过！免费检测功能改进成功！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，需要进一步优化")
        sys.exit(1)