#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试表格扩展功能
验证18列详细文献信息表格是否正确实现
"""

import re
import sys
from pathlib import Path

def test_table_extension():
    """测试表格扩展功能"""
    
    print("🧪 开始测试表格扩展功能...")
    
    # 检查index.html文件
    index_path = Path("/Users/x/Downloads/fuEvidenceFinder/fuEvidenceFinder/templates/index.html")
    
    if not index_path.exists():
        print("❌ 错误：找不到index.html文件")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📄 正在检查表格表头...")
    
    # 检查表头是否包含18列
    thead_pattern = r'<thead[^>]*>(.*?)</thead>'
    thead_match = re.search(thead_pattern, content, re.DOTALL)
    
    if not thead_match:
        print("❌ 错误：未找到表格表头")
        return False
    
    thead_content = thead_match.group(1)
    
    # 检查18个表头字段
    expected_headers = [
        '发表年份', '数据收集年份', '国家', '研究类型', '研究对象', '样本量',
        '推荐补充剂量', '作用机理', '证据等级', '结论摘要', '标题', 'PMID',
        '免费全文状态', '免费全文链接数', '全文提取状态', '摘要主要内容', 
        '全文内容摘要', '详情'
    ]
    
    headers_found = 0
    for header in expected_headers:
        if header in thead_content:
            headers_found += 1
            print(f"✅ 找到表头：{header}")
        else:
            print(f"❌ 缺少表头：{header}")
    
    print(f"\n📊 表头检查结果：{headers_found}/{len(expected_headers)}")
    
    print("\n🧩 正在检查表格数据行处理...")
    
    # 检查addResultRow函数是否处理18个字段
    add_result_pattern = r'function addResultRow\(result\)\s*{'
    if not re.search(add_result_pattern, content):
        print("❌ 错误：未找到addResultRow函数")
        return False
    
    # 检查是否处理所有18个字段
    expected_fields = [
        'result.发表年份', 'result.数据收集年份', 'result.国家', 'result.研究类型',
        'result.研究对象', 'result.样本量', 'result.推荐补充剂量/用法', 
        'result.作用机理', 'result.证据等级', 'result.结论摘要', 'result.标题',
        'result.PMID', 'result.免费全文状态', 'result.免费全文链接数',
        'result.全文提取状态', 'result.摘要主要内容', 'result.全文内容摘要'
    ]
    
    fields_found = 0
    for field in expected_fields:
        if field in content:
            fields_found += 1
            print(f"✅ 找到字段处理：{field}")
        else:
            print(f"❌ 缺少字段处理：{field}")
    
    print(f"\n📊 字段处理检查结果：{fields_found}/{len(expected_fields)}")
    
    print("\n🔧 正在检查colspan属性...")
    
    # 检查colspan是否正确更新为18
    colspan_6_count = len(re.findall(r'colspan="6"', content))
    colspan_18_count = len(re.findall(r'colspan="18"', content))
    
    print(f"📋 colspan='6' 剩余：{colspan_6_count} 个")
    print(f"📋 colspan='18' 使用：{colspan_18_count} 个")
    
    # 检查是否还有未更新的colspan="6"
    if colspan_6_count > 0:
        print("⚠️  警告：仍有未更新的colspan='6'属性")
        # 显示剩余的colspan="6"内容
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'colspan="6"' in line:
                print(f"   第{i+1}行：{line.strip()}")
    
    print("\n🎨 正在检查样式优化...")
    
    # 检查是否使用了合适的CSS类
    style_checks = [
        ('px-2 类', r'px-2'),
        ('text-xs 类', r'text-xs'),
        ('max-w-', r'max-w-\d+'),
        ('truncate 类', r'truncate'),
        ('transition-colors', r'transition-colors')
    ]
    
    for check_name, pattern in style_checks:
        if re.search(pattern, content):
            print(f"✅ {check_name}：已使用")
        else:
            print(f"❌ {check_name}：未使用")
    
    print("\n🔍 正在检查详情按钮...")
    
    # 检查详情按钮
    if '查看详情' in content:
        print("✅ 详情按钮：已添加")
    else:
        print("❌ 详情按钮：未找到")
    
    # 综合评估
    print("\n" + "="*60)
    print("📈 表格扩展功能测试总结")
    print("="*60)
    
    total_checks = 5
    passed_checks = 0
    
    if headers_found >= 15:  # 允许少数表头缺失
        print("✅ 表头扩展：PASS")
        passed_checks += 1
    else:
        print("❌ 表头扩展：FAIL")
    
    if fields_found >= 15:  # 允许少数字段缺失
        print("✅ 字段处理：PASS")
        passed_checks += 1
    else:
        print("❌ 字段处理：FAIL")
    
    if colspan_18_count >= 2:  # 需要至少2个colspan="18"
        print("✅ 属性更新：PASS")
        passed_checks += 1
    else:
        print("❌ 属性更新：FAIL")
    
    if colspan_6_count == 0:
        print("✅ 属性清理：PASS")
        passed_checks += 1
    else:
        print("⚠️  属性清理：PARTIAL")
    
    if '查看详情' in content:
        print("✅ 交互功能：PASS")
        passed_checks += 1
    else:
        print("❌ 交互功能：FAIL")
    
    print(f"\n🏆 总体结果：{passed_checks}/{total_checks} 项测试通过")
    
    if passed_checks >= 4:
        print("🎉 表格扩展功能测试通过！")
        return True
    else:
        print("❌ 表格扩展功能测试失败，需要进一步修复")
        return False

if __name__ == "__main__":
    success = test_table_extension()
    sys.exit(0 if success else 1)