#!/usr/bin/env python3
"""
测试脚本：提取免费全文并在终端显示
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fulltext_extractor import FullTextExtractor

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 测试免费全文提取功能")
    print("=" * 60)
    
    # 创建全文提取器实例
    extractor = FullTextExtractor()
    
    # 自动使用测试PMID
    pmid = "30049270"  # 已知有免费全文的PMID
    print(f"自动使用测试PMID: {pmid}")
    print("(注: 这是一个已知有免费全文的测试ID)")
    
    print(f"\n📋 正在处理PMID: {pmid}")
    print("-" * 60)
    
    try:
        # 1. 检查全文可用性
        print("1. 检查全文可用性...")
        availability = extractor.check_full_text_availability(pmid)
        print(f"   免费状态: {'✅ 是' if availability['is_free'] else '❌ 否'}")
        print(f"   消息: {availability['message']}")
        
        if not availability['is_free']:
            print("\n❌ 未找到免费全文")
            return
        
        # 2. 提取全文内容
        print("\n2. 提取全文内容...")
        extraction_result = extractor.extract_full_text_content(pmid)
        
        if not extraction_result['extraction_success']:
            print(f"\n❌ 提取失败: {extraction_result['message']}")
            return
        
        print(f"\n✅ 提取成功: {extraction_result['message']}")
        print("-" * 60)
        
        # 3. 显示提取的内容
        print("\n3. 提取的内容:")
        
        content = extraction_result['content']
        
        if 'title' in content:
            print(f"\n📝 标题:")
            print(f"   {content['title']}")
            
        if 'abstract' in content:
            print(f"\n📄 摘要:")
            abstract_text = content['abstract'][:500] + "..." if len(content['abstract']) > 500 else content['abstract']
            print(f"   {abstract_text}")
            
        if 'body_text' in content:
            print(f"\n📖 正文:")
            body_text = content['body_text'][:1000] + "..." if len(content['body_text']) > 1000 else content['body_text']
            print(f"   {body_text}")
            
        # 4. 显示调试信息
        print(f"\n📊 调试信息:")
        debug_info = extraction_result['debug_info']
        print(f"   页面标题: {debug_info['page_title']}")
        print(f"   提取元素: {', '.join(debug_info['extracted_elements'])}")
        
        print(f"\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
