#!/usr/bin/env python3
"""
完整测试脚本：从提取全文到发送给AI的完整流程
"""
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.fulltext_extractor import FullTextExtractor
from src.ai_extractor import AIExtractor


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 完整测试：从提取全文到发送给AI的流程")
    print("=" * 80)
    
    # 创建实例
    extractor = FullTextExtractor()
    ai_extractor = AIExtractor()
    
    # 测试PMID
    pmid = "30049270"
    print(f"\n📋 使用测试PMID: {pmid}")
    
    try:
        # 1. 检查全文可用性
        print("\n1️⃣ 检查全文可用性...")
        availability = extractor.check_full_text_availability(pmid)
        print(f"   ✓ 免费状态: {'✅ 是' if availability['is_free'] else '❌ 否'}")
        print(f"   ✓ 消息: {availability['message']}")
        
        if not availability['is_free']:
            print("\n❌ 未找到免费全文，无法继续测试")
            return
        
        # 2. 提取全文内容
        print("\n2️⃣ 提取全文内容...")
        extraction_result = extractor.extract_full_text_content(pmid)
        
        if not extraction_result['extraction_success']:
            print(f"\n❌ 提取失败: {extraction_result['message']}")
            return
        
        print(f"   ✓ 提取成功: {extraction_result['message']}")
        
        # 3. 显示提取的关键内容
        print("\n3️⃣ 提取的关键内容:")
        content = extraction_result['content']
        
        if 'title' in content:
            print(f"   📝 标题: {content['title']}")
            
        if 'abstract' in content:
            print(f"   📄 摘要: {content['abstract'][:600]}...")
        
        # 4. 构建发送给AI的提示词
        print("\n4️⃣ 构建发送给AI的提示词:")
        prompt = ai_extractor.build_extraction_prompt(content['abstract'], content['title'])
        print(f"   💬 提示词前500个字符:\n{prompt[:500]}...")
        
        # 5. 查看实际发送给AI的完整请求（简化版）
        print("\n5️⃣ 发送给AI的完整请求结构:")
        ai_request = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一个专业的医学文献分析助手，请只返回合法的JSON数据。"},
                {"role": "user", "content": prompt[:300] + "..."}  # 简化显示
            ],
            "max_tokens": 1500,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        print(f"   📤 请求结构:\n{json.dumps(ai_request, indent=2, ensure_ascii=False)}")
        
        # 6. 总结
        print("\n6️⃣ 总结:")
        print("   ✅ 成功提取了免费全文内容")
        print("   ✅ 成功构建了发送给AI的提示词")
        print(f"   ✅ 发送给AI的内容长度: {len(prompt)} 字符")
        print(f"   ✅ 主要包含: 标题 + 摘要 + 提取要求")
        
        print("\n=" * 80)
        print("🎉 完整流程测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
