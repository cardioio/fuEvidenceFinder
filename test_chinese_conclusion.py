#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试结论摘要字段的中文要求
验证AI提取函数是否正确实现中文结论摘要要求
"""

import sys
import os
import re
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chinese_conclusion_requirements():
    """测试结论摘要字段的中文要求"""
    
    print("🔍 测试结论摘要字段中文要求")
    print("=" * 50)
    
    # 1. 检查AI提取函数中的提示词
    print("📝 检查AI提取函数提示词...")
    try:
        with open('pubmed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查结论摘要字段的描述
        conclusion_pattern = r'\*\*结论摘要\*\*[^\n]*\n[^#]*?(?=\n\n|\n\s*[0-9]+\.|\n\s*7\.|\n\s*8\.|\Z)'
        conclusion_match = re.search(conclusion_pattern, content, re.DOTALL)
        
        if conclusion_match:
            conclusion_desc = conclusion_match.group(0).strip()
            print("✅ 找到结论摘要字段描述")
            
            # 检查是否包含中文要求
            chinese_requirements = [
                "必须用中文表达",
                "强制性要求",
                "必须使用中文",
                "不能使用英文"
            ]
            
            found_requirements = []
            for req in chinese_requirements:
                if req in conclusion_desc:
                    found_requirements.append(req)
            
            if found_requirements:
                print(f"✅ 发现中文要求: {found_requirements}")
            else:
                print("⚠️  未发现明确的中文要求")
            
        else:
            print("❌ 未找到结论摘要字段描述")
        
    except Exception as e:
        print(f"❌ 检查AI提取函数失败: {e}")
    
    # 2. 检查JSON模板中的结论摘要字段
    print("\n📋 检查JSON模板...")
    try:
        json_pattern = r'"结论摘要":\s*"[^"]*"'
        json_matches = re.findall(json_pattern, content)
        
        if json_matches:
            print("✅ 结论摘要字段已添加到JSON模板")
        else:
            print("❌ JSON模板中未发现结论摘要字段")
            
    except Exception as e:
        print(f"❌ 检查JSON模板失败: {e}")
    
    # 3. 检查验证函数更新
    print("\n🔍 检查验证函数更新...")
    try:
        validate_pattern = r'for key in \[([^\]]+)\]'
        validate_match = re.search(validate_pattern, content)
        
        if validate_match:
            key_list = validate_match.group(1)
            if '"结论摘要"' in key_list:
                print("✅ 验证函数已包含结论摘要字段")
            else:
                print("❌ 验证函数未包含结论摘要字段")
        else:
            print("❌ 未找到验证函数")
            
    except Exception as e:
        print(f"❌ 检查验证函数失败: {e}")
    
    # 4. 检查备用数据函数更新
    print("\n📦 检查备用数据函数...")
    try:
        fallback_pattern = r'"结论摘要":\s*"需人工确认"'
        fallback_match = re.search(fallback_pattern, content)
        
        if fallback_match:
            print("✅ 备用数据函数已包含结论摘要字段")
        else:
            print("❌ 备用数据函数未包含结论摘要字段")
            
    except Exception as e:
        print(f"❌ 检查备用数据函数失败: {e}")
    
    # 5. 检查数据处理逻辑更新
    print("\n🔄 检查数据处理逻辑...")
    try:
        processing_pattern = r"data\['结论摘要'\]\s*=\s*ai_extracted\.get\('结论摘要'"
        processing_match = re.search(processing_pattern, content)
        
        if processing_match:
            print("✅ 数据处理逻辑已更新为从AI提取结果获取结论摘要")
        else:
            print("❌ 数据处理逻辑未正确更新")
            
    except Exception as e:
        print(f"❌ 检查数据处理逻辑失败: {e}")
    
    # 6. 统计总结
    print("\n📊 总结检查结果")
    print("=" * 50)
    
    checks = [
        ("结论摘要字段描述", "结论摘要字段描述" in content),
        ("JSON模板包含结论摘要", '"结论摘要":' in content),
        ("验证函数更新", "validate_extracted_data" in content and '"结论摘要"' in content),
        ("备用数据函数更新", '"结论摘要": "需人工确认"' in content),
        ("数据处理逻辑更新", "ai_extracted.get('结论摘要'" in content),
        ("中文要求明确", "必须使用中文" in content or "强制" in content)
    ]
    
    passed_checks = 0
    for check_name, passed in checks:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{check_name}: {status}")
        if passed:
            passed_checks += 1
    
    print(f"\n总计: {passed_checks}/{len(checks)} 项检查通过")
    
    if passed_checks == len(checks):
        print("\n🎉 所有检查通过！结论摘要字段的中文要求已正确实现")
        return True
    else:
        print(f"\n⚠️  有 {len(checks) - passed_checks} 项检查未通过，需要进一步修复")
        return False

def test_ai_extraction_example():
    """测试AI提取函数的提示词示例"""
    
    print("\n" + "=" * 50)
    print("🔬 提示词示例验证")
    print("=" * 50)
    
    try:
        with open('pubmed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取结论摘要的提示词部分
        prompt_section = re.search(
            r'6\. \*\*结论摘要\*\*.*?(?=7\. \*\*国家\*\*|\n\n\*\*请以JSON格式)',
            content, 
            re.DOTALL
        )
        
        if prompt_section:
            prompt_text = prompt_section.group(0)
            print("📝 结论摘要提示词内容:")
            print("-" * 40)
            print(prompt_text.strip())
            print("-" * 40)
            
            # 检查关键要求
            requirements = [
                "必须用中文表达",
                "强制性要求",
                "不能使用英文",
                "基于研究结果总结中文结论"
            ]
            
            found_requirements = []
            for req in requirements:
                if req in prompt_text:
                    found_requirements.append(req)
            
            if found_requirements:
                print(f"\n✅ 发现关键要求: {found_requirements}")
            else:
                print("\n⚠️  未发现所有关键要求")
        else:
            print("❌ 未找到结论摘要提示词")
            
    except Exception as e:
        print(f"❌ 提取提示词失败: {e}")

if __name__ == "__main__":
    success = test_chinese_conclusion_requirements()
    test_ai_extraction_example()
    
    if success:
        print("\n🚀 下一步操作:")
        print("1. 重启服务器以加载更新的代码")
        print("2. 测试搜索功能验证结论摘要字段")
        print("3. 确认结论摘要以中文显示")
    else:
        print("\n❌ 需要修复发现的问题")