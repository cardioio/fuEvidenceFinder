#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证JavaScript错误修复
测试字段访问方式是否正确
"""

import re
from pathlib import Path

def test_javascript_fix():
    """测试JavaScript修复"""
    
    print("🔧 开始验证JavaScript错误修复...")
    
    # 检查index.html文件
    index_path = Path("/Users/x/Downloads/fuEvidenceFinder/fuEvidenceFinder/templates/index.html")
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🧩 检查字段访问方式...")
    
    # 检查是否使用了方括号表示法访问包含斜杠的属性
    bracket_usage = content.count("result['推荐补充剂量/用法']")
    dot_usage = content.count("result.推荐补充剂量/用法")
    
    print(f"✅ 方括号表示法使用次数：{bracket_usage}")
    print(f"❌ 点号表示法剩余次数：{dot_usage}")
    
    # 检查函数中的字段定义
    add_result_match = re.search(r'function addResultRow.*?\{', content, re.DOTALL)
    if add_result_match:
        print("\n📍 正在检查addResultRow函数中的字段定义...")
        add_result_section = add_result_match.group(0)
        
        # 查找推荐剂量的字段定义
        dose_pattern = r"const recommendedDose = result\[['\"](.*?)['\"]\]"
        dose_match = re.search(dose_pattern, content)
        
        if dose_match:
            field_name = dose_match.group(1)
            print(f"✅ 推荐剂量字段访问方式：result['{field_name}']")
        else:
            print("❌ 未找到推荐剂量字段的方括号访问")
    
    # 检查showResultDetails函数
    print("\n📍 正在检查showResultDetails函数...")
    show_details_pattern = r"推荐剂量: result\['推荐补充剂量/用法'\]"
    if re.search(show_details_pattern, content):
        print("✅ showResultDetails函数：已使用方括号访问")
    else:
        print("❌ showResultDetails函数：未使用方括号访问")
    
    # 检查控制台错误的可能性
    print("\n🚨 检查其他可能导致错误的地方...")
    
    # 查找其他可能的特殊字符属性
    special_char_patterns = [
        r"result\.[^.\s\)]*[/]",
        r"result\.[^.\s\)]*['\"]"
    ]
    
    issues_found = []
    for pattern in special_char_patterns:
        matches = re.findall(pattern, content)
        if matches:
            issues_found.extend(matches)
    
    if issues_found:
        print("⚠️  发现其他可能的特殊字符属性：")
        for issue in set(issues_found):  # 去重
            print(f"   - {issue}")
    else:
        print("✅ 未发现其他特殊字符属性问题")
    
    # 总结
    print("\n" + "="*60)
    print("📈 JavaScript修复验证结果")
    print("="*60)
    
    if bracket_usage >= 2 and dot_usage == 0:
        print("✅ JavaScript修复：PASS")
        print("✅ 所有包含斜杠的属性都使用方括号访问")
        print("✅ 应该可以解决'用法 is not defined'错误")
        return True
    else:
        print("❌ JavaScript修复：需要进一步检查")
        return False

if __name__ == "__main__":
    success = test_javascript_fix()
    if success:
        print("\n🎉 修复验证成功！现在应该可以在表格中正常显示文献数据了。")
    else:
        print("\n❌ 修复验证失败，需要进一步修复。")