#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端流式搜索功能
模拟前端的 fetch API 流式数据处理
"""

import requests
import json
import time

def test_streaming_search():
    """测试流式搜索功能"""
    print("🔍 开始测试流式搜索功能...")
    
    url = "http://localhost:5001/stream_search?keyword=mct oil"
    
    try:
        # 发送请求并接收流数据
        response = requests.get(url, stream=True, timeout=30)
        
        if response.status_code == 200:
            print("✅ 连接成功，开始接收流数据...")
            
            logs_count = 0
            results_count = 0
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                line = line.decode('utf-8').strip()
                
                if line.startswith('data: '):
                    try:
                        json_str = line[6:]  # 移除 'data: ' 前缀
                        data = json.loads(json_str)
                        
                        if data.get('type') == 'log' and data.get('content'):
                            logs_count += 1
                            content = data['content']
                            print(f"📝 [{content.get('timestamp', '')}] [{content.get('level', '').upper()}] {content.get('message', '')}")
                            
                        elif data.get('type') == 'row' and data.get('content'):
                            results_count += 1
                            result = data['content']
                            title = result.get('标题', 'N/A')[:50]
                            print(f"📊 结果 {results_count}: {title}...")
                            
                        elif data.get('type') == 'end':
                            print(f"🎉 搜索完成！共收到 {logs_count} 条日志，{results_count} 条结果")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析错误: {e}")
                        print(f"原始数据: {line}")
                        continue
                        
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

if __name__ == "__main__":
    test_streaming_search()