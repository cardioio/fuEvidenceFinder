#!/usr/bin/env python3
"""
专门测试AI API调用功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pubmed import extract_info_with_ai

def test_ai_only():
    """
    测试AI提取功能 - 使用正则表达式难以处理的摘要
    """
    # 故意使用正则表达式难以处理的摘要
    difficult_abstract = """
    This study investigated the metabolic effects of medium-chain triglyceride supplementation 
    in a group of individuals with varying health statuses. The intervention involved regular 
    consumption of MCT-containing products over an extended period. Results indicated significant 
    changes in energy metabolism and body composition markers. The participants showed improved 
    metabolic markers and experienced various physiological adaptations. These findings suggest 
    potential benefits for metabolic health management strategies.
    """
    
    print("=" * 60)
    print("专门测试AI API调用功能")
    print("=" * 60)
    print(f"摘要长度: {len(difficult_abstract)} 字符")
    print("摘要内容:")
    print(difficult_abstract)
    print("\n" + "-" * 40)
    
    # 直接调用AI提取，绕过正则表达式检查
    print("直接调用AI提取功能...")
    ai_result = extract_info_with_ai(difficult_abstract)
    
    print("\nAI提取结果:")
    for key, value in ai_result.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_ai_only()