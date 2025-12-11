#!/usr/bin/env python3
"""
完整功能演示：PubMed搜索 + 全文提取
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pubmed import ENABLE_FULLTEXT_EXTRACTION, get_user_search_term, search_pubmed, fetch_details, parse_record
import pandas as pd

def demo_full_search_with_fulltext():
    """
    演示完整的PubMed搜索流程，包括全文提取功能
    """
    print("=" * 80)
    print("🔬 PubMed文献搜索 + 全文提取功能完整演示")
    print("=" * 80)
    
    # 设置搜索参数
    search_term = "MCT medium chain triglycerides"  # 使用简短搜索词以快速演示
    max_results = 5  # 限制结果数量以快速演示
    
    print(f"📝 搜索词: {search_term}")
    print(f"📊 最大结果数: {max_results}")
    print(f"🔍 全文提取功能: {'启用' if ENABLE_FULLTEXT_EXTRACTION else '禁用'}")
    
    # 手动启用全文提取功能
    import pubmed
    pubmed.ENABLE_FULLTEXT_EXTRACTION = True
    print(f"✅ 已启用全文提取功能进行演示")
    
    print("\n" + "="*80)
    print("开始搜索流程...")
    print("="*80)
    
    try:
        # 1. 搜索PubMed
        print(f"\n🔍 步骤1: 搜索PubMed...")
        ids = search_pubmed(search_term, max_results)
        
        if ids:
            print(f"✅ 找到 {len(ids)} 篇相关文献")
            
            # 2. 获取详情
            print(f"\n📋 步骤2: 获取文献详细信息...")
            articles = fetch_details(ids)
            print(f"✅ 成功获取 {len(articles)} 篇文献详情")
            
            # 3. 解析数据并提取全文
            print(f"\n🔬 步骤3: 解析文献数据并检查全文...")
            results = []
            
            for i, article in enumerate(articles):
                print(f"\n  处理文献 {i+1}/{len(articles)}...")
                try:
                    result = parse_record(article)
                    results.append(result)
                except Exception as e:
                    print(f"  ❌ 处理第{i+1}篇文献时出错: {e}")
                    continue
            
            # 4. 生成Excel文件
            if results:
                print(f"\n📊 步骤4: 生成Excel文件...")
                df = pd.DataFrame(results)
                
                # 显示统计信息
                total_papers = len(df)
                free_fulltext_count = df['免费全文状态'].sum() if '免费全文状态' in df.columns else 0
                successful_extraction_count = df['全文提取状态'].sum() if '全文提取状态' in df.columns else 0
                
                print(f"✅ 成功处理 {total_papers} 篇文献")
                print(f"  - 有免费全文: {free_fulltext_count} 篇")
                print(f"  - 成功提取全文: {successful_extraction_count} 篇")
                
                # 显示示例数据
                print(f"\n📋 示例文献信息:")
                if total_papers > 0:
                    sample = df.iloc[0]
                    print(f"  标题: {sample.get('标题', 'N/A')[:80]}...")
                    print(f"  PMID: {sample.get('PMID', 'N/A')}")
                    print(f"  年份: {sample.get('发表年份', 'N/A')}")
                    print(f"  国家: {sample.get('国家', 'N/A')}")
                    if '免费全文状态' in df.columns:
                        print(f"  免费全文: {'是' if sample.get('免费全文状态') else '否'}")
                    if '免费全文链接数' in df.columns:
                        print(f"  免费链接数: {sample.get('免费全文链接数', 0)}")
                    if '全文提取状态' in df.columns:
                        print(f"  全文提取: {'成功' if sample.get('全文提取状态') else '失败'}")
                
                # 生成文件名
                filename = f"Demo_Search_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(filename, index=False)
                print(f"\n✅ 成功导出Excel文件: {filename}")
                print(f"📊 文件包含 {len(df)} 篇文献的详细信息")
                
                # 显示列信息
                print(f"\n📋 Excel文件包含的列:")
                for i, col in enumerate(df.columns, 1):
                    print(f"  {i:2d}. {col}")
                
            else:
                print("❌ 没有成功处理任何文献")
                
        else:
            print("❌ 未找到相关文献")
            
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("🎉 演示完成！")
    print("="*80)

if __name__ == "__main__":
    demo_full_search_with_fulltext()