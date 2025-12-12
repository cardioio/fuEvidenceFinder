#!/usr/bin/env python3
"""
直接打印提取的完整免费全文内容和发送给AI的完整提示词
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
    print("=" * 100)
    print("📄 打印提取并发送给AI的完整免费全文")
    print("=" * 100)
    
    # 创建实例
    extractor = FullTextExtractor()
    ai_extractor = AIExtractor()
    
    # 测试PMID
    pmid = "30049270"
    print(f"\n🔍 处理PMID: {pmid}")
    
    try:
        # 1. 提取全文内容
        print("\n1️⃣ 正在提取全文内容...")
        extraction_result = extractor.extract_full_text_content(pmid)
        
        if not extraction_result['extraction_success']:
            print(f"\n❌ 提取失败: {extraction_result['message']}")
            return
        
        print(f"   ✅ 提取成功！")
        
        # 2. 获取提取的完整内容
        print("\n2️⃣ 提取的完整免费全文内容:")
        print("=" * 60)
        
        content = extraction_result['content']
        
        # 打印所有提取的字段
        for key, value in content.items():
            if value and isinstance(value, str):
                print(f"\n🔹 {key}:")
                print("-" * 40)
                
                # 如果内容太长，分段显示
                if len(value) > 1000:
                    chunks = [value[i:i+1000] for i in range(0, len(value), 1000)]
                    for i, chunk in enumerate(chunks):
                        print(chunk)
                        if i < len(chunks) - 1:
                            print("...")
                else:
                    print(value)
        
        print("=" * 60)
        
        # 3. 生成发送给AI的完整提示词
        print("\n3️⃣ 发送给AI的完整提示词:")
        print("=" * 60)
        
        # 使用摘要或正文（优先使用摘要）
        text_for_ai = content.get('abstract', '')
        if not text_for_ai and 'body_text' in content:
            text_for_ai = content['body_text'][:5000]  # 限制长度
        
        if not text_for_ai:
            print("❌ 没有可用于AI分析的文本")
            return
        
        prompt = ai_extractor.build_extraction_prompt(text_for_ai, content.get('title', ''))
        
        # 打印完整提示词
        print(prompt)
        
        print("=" * 60)
        
        # 4. 统计信息
        print("\n4️⃣ 统计信息:")
        print(f"   ✓ 提取的字段数量: {len(content)}")
        print(f"   ✓ 发送给AI的内容长度: {len(prompt)} 字符")
        
        # 5. 保存到文件（可选）
        output_file = f"fulltext_ai_content_{pmid}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'pmid': pmid,
                'extracted_content': content,
                'prompt_sent_to_ai': prompt
            }, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ 内容已保存到: {output_file}")
        
        print("\n" + "=" * 100)
        print("🎉 完成！成功打印了提取并发送给AI的免费全文内容")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
