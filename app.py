#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web 应用 - 文献检索系统
基于 Flask 框架的现代化 Web 界面
集成 PubMed 搜索功能
"""

from flask import Flask, render_template, Response, request, jsonify
import json
import time
import threading
import logging
import sys
import os
from datetime import datetime

# 导入 PubMed 搜索相关函数
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pubmed import search_pubmed, fetch_details, parse_record, ENABLE_FULLTEXT_EXTRACTION

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 生产环境请使用更强的密钥

# 全局变量存储搜索状态
search_status = {
    'is_running': False,
    'current_keyword': '',
    'logs': [],
    'results': []
}

def add_log(message, level='info'):
    """添加日志到全局状态"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    search_status['logs'].append(log_entry)
    logger.info(f"[{timestamp}] {message}")

def process_search(keyword, max_results=20, enable_fulltext=True):
    """
    生成器函数：实际的 PubMed 搜索过程
    将 print() 语句替换为 yield JSON 日志消息
    在 parse_record 后立即 yield 数据行
    
    Args:
        keyword: 搜索关键词
        max_results: 最大结果数量 (1-100)
        enable_fulltext: 是否启用全文搜索
    """
    # 保存原始的 print 函数
    original_print = print
    
    def yield_log(message, level='info'):
        """Yield 日志消息而不是打印"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_data = {
            'type': 'log',
            'content': {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }
        }
        yield f"data: {json.dumps(log_data, ensure_ascii=False)}\n\n"
    
    # 临时替换 print 函数
    def custom_print(*args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        return list(yield_log(message))
    
    # 将 print 替换为自定义函数
    import builtins
    builtins.print = custom_print
    
    try:
        # 记录搜索配置
        yield from yield_log(f"🔍 搜索配置 - 关键词: {keyword}")
        yield from yield_log(f"📊 搜索配置 - 最大结果数: {max_results}篇")
        yield from yield_log(f"📄 搜索配置 - 原文搜索: {'开启' if enable_fulltext else '关闭'}")
        
        # 开始搜索流程
        yield from yield_log(f"🚀 开始搜索关键词: {keyword}")
        
        # 1. 搜索 PubMed
        yield from yield_log(f"🔍 正在搜索: {keyword.strip()}...")
        ids = search_pubmed(keyword, max_results)  # 使用参数化的最大结果数
        
        if not ids:
            yield from yield_log("❌ 未找到相关文献，请检查搜索词是否正确", 'warning')
            return
        
        yield from yield_log(f"✅ 找到 {len(ids)} 篇相关文献，开始获取详细信息...")
        
        # 2. 获取详情
        yield from yield_log(f"📥 正在获取 {len(ids)} 篇文献的详细信息...")
        articles = fetch_details(ids)
        
        if not articles:
            yield from yield_log("❌ 获取文献详情失败", 'error')
            return
        
        yield from yield_log(f"✅ 成功获取 {len(articles)} 篇文献详情，开始解析数据...")
        
        # 3. 解析数据 - 逐条处理并 yield
        results_count = 0
        for i, article in enumerate(articles):
            # 检查是否需要停止搜索（在处理过程中检查）
            if not search_status['is_running']:
                yield from yield_log("⏹️ 搜索被用户中断", 'warning')
                yield from yield_log(f"📊 已处理 {results_count} 篇文献", 'info')
                break
            
            yield from yield_log(f"⚙️ 正在处理文献 {i+1}/{len(articles)}...")
            
            try:
                # 解析单篇文献
                data = parse_record(article)
                results_count += 1
                
                # 立即 yield 数据行
                row_data = {
                    'type': 'row',
                    'content': data
                }
                yield f"data: {json.dumps(row_data, ensure_ascii=False)}\n\n"
                
                yield from yield_log(f"✅ 文献 {i+1} 处理完成: {data.get('标题', 'N/A')[:50]}...")
                
                # 短暂停顿以允许用户中断
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = f"处理第 {i+1} 篇文献时出错: {str(e)}"
                yield from yield_log(error_msg, 'error')
                logger.error(error_msg)
                continue
        
        # 搜索完成
        yield from yield_log(f"🎉 搜索完成！共处理 {results_count} 篇文献", 'success')
        
    except Exception as e:
        error_msg = f"搜索过程中发生错误: {str(e)}"
        yield from yield_log(error_msg, 'error')
        logger.error(error_msg)
    finally:
        # 恢复原始的 print 函数
        builtins.print = original_print
        search_status['is_running'] = False

@app.route('/')
def index():
    """主页面路由"""
    return render_template('index.html')

@app.route('/stream_search')
def stream_search():
    """流式搜索响应路由 - 使用实际的 PubMed 搜索"""
    keyword = request.args.get('keyword', '')
    max_results = request.args.get('max_results', default=20, type=int)
    enable_fulltext = request.args.get('enable_fulltext', default='true').lower() == 'true'
    
    # 参数验证
    if not keyword:
        return jsonify({'error': '缺少关键词参数'}), 400
    
    if max_results < 1 or max_results > 100:
        return jsonify({'error': '最大结果数量必须在1-100之间'}), 400
    
    # 重置搜索状态
    global search_status
    search_status = {
        'is_running': True,
        'current_keyword': keyword,
        'max_results': max_results,
        'enable_fulltext': enable_fulltext,
        'logs': [],
        'results': []
    }
    
    def generate():
        """生成流式响应"""
        try:
            # 直接使用 process_search 生成器，传递参数化配置
            for data_chunk in process_search(keyword, max_results, enable_fulltext):
                if not search_status['is_running']:
                    # 发送用户停止信号
                    stop_data = {
                        'type': 'stopped',
                        'content': {'message': '搜索已停止'}
                    }
                    yield f"data: {json.dumps(stop_data, ensure_ascii=False)}\n\n"
                    break
                
                yield data_chunk
            
            # 发送结束信号
            end_data = {'type': 'end'}
            yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式搜索出错: {e}")
            error_data = {
                'type': 'error',
                'content': {'message': f'搜索过程中发生错误: {str(e)}'}
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',  # 使用 SSE 格式
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.route('/search', methods=['POST'])
def search():
    """搜索接口（可选的同步接口）"""
    data = request.get_json()
    keyword = data.get('keyword', '') if data else ''
    
    if not keyword:
        return jsonify({'error': '缺少关键词'}), 400
    
    # 这里可以集成实际的 pubmed.py 搜索逻辑
    # 目前返回模拟结果
    return jsonify({
        'success': True,
        'message': f'开始搜索: {keyword}',
        'keyword': keyword
    })

@app.route('/status')
def status():
    """获取当前搜索状态"""
    return jsonify(search_status)

@app.route('/stop_search', methods=['POST'])
def stop_search():
    """停止搜索"""
    search_status['is_running'] = False
    add_log("搜索已手动停止", 'warning')
    return jsonify({'success': True, 'message': '搜索已停止'})

if __name__ == '__main__':
    print("🚀 启动 Flask 应用...")
    print("📱 访问地址: http://localhost:5001")
    print("🔍 搜索接口: POST /search")
    print("📡 流式接口: GET /stream_search?keyword=关键词")
    
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)