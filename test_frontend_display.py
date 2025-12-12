#!/usr/bin/env python3
"""
前端显示逻辑测试脚本
测试AI返回的标题和翻译标题在前端的显示
"""

import json
from src.ai_extractor import extract_info_with_ai

def test_frontend_display():
    """测试前端显示逻辑"""
    print("🧪 测试前端显示逻辑")
    print("=" * 50)
    
    # 模拟不同的测试场景
    test_cases = [
        {
            "name": "正常标题测试",
            "data": {
                "title": "Effects of Vitamin D supplementation on cardiovascular health",
                "abstract": "This study examines the effects of Vitamin D supplementation on cardiovascular health in adults aged 50-70. We conducted a randomized controlled trial with 200 participants over 12 months. Results show significant improvements in blood pressure and lipid profiles.",
                "pmid": "12345678"
            },
            "expected": "应该包含原文标题和翻译标题"
        },
        {
            "name": "空标题测试", 
            "data": {
                "title": "",
                "abstract": "This study examines the effects of Vitamin D supplementation on cardiovascular health in adults aged 50-70. We conducted a randomized controlled trial with 200 participants over 12 months. Results show significant improvements in blood pressure and lipid profiles.",
                "pmid": "12345679"
            },
            "expected": "应该使用默认标题值"
        },
        {
            "name": "无标题测试",
            "data": {
                "abstract": "This study examines the effects of Vitamin D supplementation on cardiovascular health in adults aged 50-70. We conducted a randomized controlled trial with 200 participants over 12 months. Results show significant improvements in blood pressure and lipid profiles.",
                "pmid": "12345680"
            },
            "expected": "应该使用默认标题值"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试案例 {i}: {test_case['name']}")
        print(f"   期望结果: {test_case['expected']}")
        
        try:
            # 调用AI提取功能
            result = extract_info_with_ai(
                abstract_text=test_case['data']['abstract'],
                title=test_case['data'].get('title', '')
            )
            
            # 检查关键字段
            has_original_title = '原文标题' in result
            has_translated_title = '翻译标题' in result
            original_title = result.get('原文标题', 'N/A')
            translated_title = result.get('翻译标题', 'N/A')
            
            print(f"   ✅ 原文标题字段存在: {has_original_title}")
            print(f"   ✅ 翻译标题字段存在: {has_translated_title}")
            print(f"   📝 原文标题: {original_title}")
            print(f"   📝 翻译标题: {translated_title}")
            
            # 验证前端显示兼容性
            frontend_title = result.get('标题') or result.get('原文标题') or '-'
            frontend_translated_title = result.get('翻译标题') or '-'
            
            print(f"   🖥️  前端显示 - 原文标题: {frontend_title}")
            print(f"   🖥️  前端显示 - 翻译标题: {frontend_translated_title}")
            
            if has_original_title and has_translated_title:
                print(f"   ✅ 测试通过")
                success_count += 1
            else:
                print(f"   ❌ 测试失败: 缺少必要字段")
                
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
    
    print(f"\n📊 测试总结")
    print(f"   总测试案例: {total_count}")
    print(f"   成功案例: {success_count}")
    print(f"   成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print(f"   🎉 所有测试通过！前端显示逻辑工作正常。")
        return True
    else:
        print(f"   ⚠️  部分测试失败，需要检查实现。")
        return False

if __name__ == "__main__":
    print("🚀 开始前端显示逻辑测试")
    test_frontend_display()
    print("✨ 测试完成")