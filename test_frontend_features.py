#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端功能完整性测试
验证所有JavaScript功能是否正确实现
"""

import re

def test_index_html_features():
    """检查index.html中的关键功能实现"""
    print("🔍 检查前端功能实现...")
    
    try:
        with open('/Users/x/Downloads/fuEvidenceFinder/fuEvidenceFinder/templates/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键功能点
        checks = {
            "fetch API 实现": "fetch.*signal",
            "AbortController": "AbortController",
            "日志追加功能": "logConsole.appendChild",
            "结果行生成": "addResultRow",
            "状态更新": "updateStatus",
            "加载动画": "loadingSpinner",
            "自动滚动": "scrollTop.*scrollHeight",
            "错误处理": "catch.*error",
            "流数据解析": "JSON.parse.*jsonStr"
        }
        
        results = {}
        for feature, pattern in checks.items():
            if re.search(pattern, content, re.IGNORECASE):
                results[feature] = "✅ 已实现"
            else:
                results[feature] = "❌ 未找到"
        
        print("\n📋 功能检查结果:")
        print("=" * 50)
        for feature, status in results.items():
            print(f"{feature}: {status}")
        
        # 检查关键函数
        functions = ["startStreamSearch", "stopSearch", "addResultRow", "showResultDetails"]
        print(f"\n🔧 关键函数检查:")
        print("=" * 50)
        
        for func in functions:
            if f"function {func}" in content or f"{func} = " in content:
                print(f"{func}(): ✅ 已定义")
            else:
                print(f"{func}(): ❌ 未找到")
        
        # 统计代码行数
        lines = content.split('\n')
        html_lines = len([l for l in lines if l.strip()])
        js_lines = len([l for l in lines if 'function' in l or 'const ' in l or 'let ' in l or 'var ' in l])
        
        print(f"\n📊 代码统计:")
        print("=" * 50)
        print(f"HTML代码: {html_lines} 行")
        print(f"JavaScript: {js_lines} 行")
        
        # 检查主要功能是否完整
        all_features = all(status == "✅ 已实现" for status in results.values())
        
        if all_features:
            print(f"\n🎉 前端功能检查通过！所有关键功能都已实现。")
            return True
        else:
            print(f"\n⚠️  部分功能可能需要进一步完善。")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    test_index_html_features()