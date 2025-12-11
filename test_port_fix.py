#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试端口修复后的流式搜索功能
验证前端URL修正是否成功
"""

import requests
import json
import time
import re
from typing import Dict, Any

def test_port_fix():
    """测试端口修复是否成功"""
    
    print("🔧 测试端口修复效果")
    print("=" * 50)
    
    # 测试端口5001是否可用
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        print("✅ 端口5001服务器正常响应")
        print(f"   状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 端口5001服务器无响应: {e}")
        return False
    
    # 测试流式接口
    try:
        print("\n📡 测试流式搜索接口...")
        url = "http://localhost:5001/stream_search?keyword=test"
        response = requests.get(url, timeout=10, stream=True)
        
        if response.status_code == 200:
            print("✅ 流式接口响应正常")
            print(f"   Content-Type: {response.headers.get('Content-Type', '未知')}")
            
            # 检查前几行流数据
            line_count = 0
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line_count += 1
                        print(f"   流数据 {line_count}: {line[:100]}...")
                        
                        if line_count >= 3:  # 只检查前3行
                            break
            
            if line_count > 0:
                print("✅ 流式数据格式正确")
            else:
                print("⚠️  未检测到流式数据")
        else:
            print(f"❌ 流式接口响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 流式接口测试失败: {e}")
        return False
    
    # 检查前端代码端口修复
    print("\n🔍 检查前端代码端口修复...")
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找stream_search URL
        pattern = r'const url = `http://localhost:(\d+)/stream_search'
        match = re.search(pattern, content)
        
        if match:
            port = match.group(1)
            print(f"✅ 前端URL已修正为端口: {port}")
            
            if port == "5001":
                print("✅ 端口修正正确")
            else:
                print(f"⚠️  端口修正可能不完整: 期望5001，实际{port}")
                return False
        else:
            print("❌ 未找到stream_search URL配置")
            return False
            
    except Exception as e:
        print(f"❌ 检查前端代码失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 端口修复测试完成！")
    print("💡 建议: 现在可以重新测试流式搜索功能")
    
    return True

def test_server_logs():
    """测试服务器日志查看"""
    print("\n📋 服务器运行状态检查")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:5001/status", timeout=5)
        if response.status_code == 200:
            print("✅ 状态接口正常")
            try:
                status_data = response.json()
                print(f"   服务器状态: {status_data}")
            except:
                print(f"   响应内容: {response.text[:200]}")
        else:
            print(f"⚠️  状态接口异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 状态接口无响应: {e}")

if __name__ == "__main__":
    success = test_port_fix()
    test_server_logs()
    
    if success:
        print("\n🚀 下一步操作:")
        print("1. 在浏览器中访问: http://localhost:5001")
        print("2. 输入搜索关键词测试流式搜索")
        print("3. 检查控制台是否还有错误")