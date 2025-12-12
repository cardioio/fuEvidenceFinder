#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标题翻译功能测试脚本
测试AI提取器的标题翻译集成功能
"""

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ai_extractor import extract_info_with_ai

def test_title_translation():
    """测试标题翻译功能"""
    print("🧪 开始测试标题翻译集成功能...")
    
    # 测试案例1：包含标题的文献
    test_cases = [
        {
            "title": "Vitamin D supplementation and bone health in elderly adults: A randomized controlled trial",
            "abstract": "This randomized controlled trial investigated the effects of vitamin D supplementation on bone health in 500 elderly adults aged 65-80 years. Participants received either 1000 IU vitamin D3 daily or placebo for 12 months. The study found that vitamin D supplementation significantly improved bone mineral density and reduced fracture risk."
        },
        {
            "title": "Effects of omega-3 fatty acids on cardiovascular disease prevention: A meta-analysis",
            "abstract": "This meta-analysis of 25 randomized controlled trials examined the effects of omega-3 fatty acid supplementation on cardiovascular disease prevention. The analysis included 15,000 participants and found that omega-3 supplementation reduced the risk of cardiovascular events by 15%."
        },
        {
            "title": "",
            "abstract": "This study investigated the effects of calcium supplementation on bone health in postmenopausal women. A total of 200 participants were randomly assigned to receive calcium supplements or placebo for 24 months."
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试案例 {i}:")
        print(f"  原文标题: {test_case['title'] or '无标题'}")
        
        try:
            # 调用AI提取器
            result = extract_info_with_ai(test_case['abstract'], test_case['title'])
            
            # 检查返回结果
            if result:
                print(f"  ✅ AI提取成功")
                print(f"  📝 原文标题: {result.get('原文标题', '未返回')}")
                print(f"  🇨🇳 翻译标题: {result.get('翻译标题', '未返回')}")
                print(f"  🧬 研究对象: {result.get('研究对象', '未返回')}")
                print(f"  📊 样本量: {result.get('样本量', '未返回')}")
                
                # 验证标题字段
                if '原文标题' in result and '翻译标题' in result:
                    success_count += 1
                    print(f"  ✅ 标题字段验证通过")
                else:
                    print(f"  ❌ 标题字段缺失")
            else:
                print(f"  ❌ AI提取失败")
                
        except Exception as e:
            print(f"  ❌ 测试过程中发生错误: {e}")
    
    print(f"\n📊 测试结果汇总:")
    print(f"  总测试案例: {total_count}")
    print(f"  成功案例: {success_count}")
    print(f"  成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("  🎉 所有测试案例通过！标题翻译功能集成成功")
        return True
    else:
        print("  ⚠️ 部分测试案例失败，需要检查实现")
        return False

if __name__ == "__main__":
    success = test_title_translation()
    sys.exit(0 if success else 1)