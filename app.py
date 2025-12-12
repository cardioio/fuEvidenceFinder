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
from queue import Queue

# 导入 PubMed 搜索相关函数
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pubmed import search_pubmed, fetch_details, parse_record, ENABLE_FULLTEXT_EXTRACTION

# 配置日志 - 启用调试模式
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')
logger = logging.getLogger(__name__)

# 创建自定义日志处理器，将日志发送到前端
class FrontendLogHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.encoding = 'utf-8'
    
    def emit(self, record):
        try:
            # 格式化日志记录
            message = self.format(record)
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # 根据日志级别映射到前端使用的级别
            level_map = {
                logging.DEBUG: 'debug',
                logging.INFO: 'info',
                logging.WARNING: 'warning',
                logging.ERROR: 'error',
                logging.CRITICAL: 'error'
            }
            level = level_map.get(record.levelno, 'info')
            
            # 创建日志数据
            log_data = {
                'type': 'log',
                'content': {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message,
                    'module': record.name,
                    'line': record.lineno,
                    'function': record.funcName
                }
            }
            
            # 将日志添加到队列
            self.queue.put(log_data)
            
        except Exception as e:
            print(f"日志处理器出错: {e}")

# 创建全局线程安全队列
log_queue = Queue()

# 创建前端日志处理器实例
frontend_handler = FrontendLogHandler(log_queue)
frontend_handler.setLevel(logging.DEBUG)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')
frontend_handler.setFormatter(formatter)

# 为根日志记录器添加前端处理器
root_logger = logging.getLogger()
root_logger.addHandler(frontend_handler)

# 设置Flask应用的日志级别
logging.getLogger('flask').setLevel(logging.INFO)  # Flask自身日志设为INFO避免过多噪音

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

def process_search(keyword, max_results=20, enable_fulltext=True, data_queue=None):
    """
    实际的 PubMed 搜索过程，将结果和日志放入队列
    
    Args:
        keyword: 搜索关键词
        max_results: 最大结果数量 (1-100)
        enable_fulltext: 是否启用全文搜索
        data_queue: 用于传递搜索结果和日志的队列
    """
    def add_log(message, level='info'):
        """将日志添加到队列"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_data = {
            'type': 'log',
            'content': {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }
        }
        data_queue.put(log_data)
    
    try:
        # 记录搜索配置
        add_log(f"🔍 搜索配置 - 关键词: {keyword}")
        add_log(f"📊 搜索配置 - 最大结果数: {max_results}篇")
        add_log(f"📄 搜索配置 - 原文搜索: {'开启' if enable_fulltext else '关闭'}")
        
        # 开始搜索流程
        add_log(f"🚀 开始搜索关键词: {keyword}")
        
        # 1. 搜索 PubMed
        add_log(f"🔍 正在搜索: {keyword.strip()}...")
        ids = search_pubmed(keyword, max_results)  # 使用参数化的最大结果数
        
        if not ids:
            add_log("❌ 未找到相关文献，请检查搜索词是否正确", 'warning')
            return
        
        add_log(f"✅ 找到 {len(ids)} 篇相关文献，开始获取详细信息...")
        
        # 2. 获取详情
        add_log(f"📥 正在获取 {len(ids)} 篇文献的详细信息...")
        articles = fetch_details(ids)
        
        if not articles:
            add_log("❌ 获取文献详情失败", 'error')
            return
        
        add_log(f"✅ 成功获取 {len(articles)} 篇文献详情，开始解析数据...")
        
        # 3. 解析数据 - 逐条处理并放入队列
        results_count = 0
        fulltext_success_count = 0
        paid_count = 0
        failed_count = 0
        ai_success_count = 0
        
        for i, article in enumerate(articles):
            # 检查是否需要停止搜索（在处理过程中检查）
            if not search_status['is_running']:
                add_log("⏹️ 搜索被用户中断", 'warning')
                add_log(f"📊 已处理 {results_count} 篇文献", 'info')
                break
            
            add_log(f"⚙️ 正在处理文献 {i+1}/{len(articles)}...")
            
            try:
                # 解析单篇文献
                data = parse_record(article, enable_fulltext)
                results_count += 1
                
                # 实时显示全文处理状态
                if enable_fulltext:
                    free_status = data.get('免费全文状态', '未检查')
                    if free_status == '免费':
                        fulltext_success_count += 1
                        add_log(f"  📤 文献 {i+1} 检测到免费全文，开始内容提取...", 'info')
                    elif free_status == '付费':
                        paid_count += 1
                        add_log(f"  💰 文献 {i+1} 仅付费全文，跳过免费内容", 'warning')
                    else:
                        failed_count += 1
                        add_log(f"  ⚠️ 文献 {i+1} 免费状态检查失败: {free_status}", 'warning')
                
                # 实时显示AI处理状态
                if enable_fulltext:  # 只有启用了全文提取才会进行AI提取
                    if data.get('AI提取状态') == '成功':
                        ai_success_count += 1
                        add_log(f"  🤖 文献 {i+1} AI提取完成", 'success')
                    elif data.get('AI提取状态') == '失败':
                        add_log(f"  ❌ 文献 {i+1} AI提取失败", 'error')
                
                # 立即将数据行放入队列
                row_data = {
                    'type': 'row',
                    'content': data
                }
                data_queue.put(row_data)
                
                # 显示处理进度汇总
                add_log(f"✅ 文献 {i+1} 处理完成: {data.get('标题', 'N/A')[:50]}...")
                
                if enable_fulltext:
                    add_log(f"  📊 处理进度 - 全文: {fulltext_success_count}/{results_count}, AI: {ai_success_count}/{results_count}", 'info')
                
                # 短暂停顿以允许用户中断
                time.sleep(0.1)
                
                # 立即检查停止状态（快速响应）
                if not search_status['is_running']:
                    add_log("⏹️ 搜索被用户中断", 'warning')
                    add_log(f"📊 已处理 {results_count} 篇文献", 'info')
                    break
                
            except Exception as e:
                error_msg = f"处理第 {i+1} 篇文献时出错: {str(e)}"
                add_log(error_msg, 'error')
                logger.error(error_msg)
                continue
        
        # 搜索完成 - 显示详细汇总
        add_log(f"🎉 搜索完成！共处理 {results_count} 篇文献", 'success')
        
        if enable_fulltext:
            # 确保付费全文和失败数的统计正确
            # 如果没有明确标记为免费或付费，就视为失败
            total_processed = fulltext_success_count + paid_count + failed_count
            if total_processed < results_count:
                failed_count += (results_count - total_processed)
            
            add_log(f"📊 全文处理统计:", 'info')
            add_log(f"  ✅ 免费全文: {fulltext_success_count} 篇", 'success')
            add_log(f"  💰 付费全文: {paid_count} 篇", 'warning')
            add_log(f"  ❌ 检查失败: {failed_count} 篇", 'error')
            
            add_log(f"🔍 搜索任务完成，用户可查看结果表格", 'success')
        
    except Exception as e:
        error_msg = f"搜索过程中发生错误: {str(e)}"
        add_log(error_msg, 'error')
        logger.error(error_msg)
    finally:
        search_status['is_running'] = False
        # 发送结束信号
        end_data = {'type': 'end'}
        data_queue.put(end_data)

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
        # 创建用于搜索数据的队列
        data_queue = Queue()
        
        # 创建并启动搜索线程
        search_thread = threading.Thread(
            target=process_search,
            args=(keyword, max_results, enable_fulltext, data_queue),
            daemon=True
        )
        search_thread.start()
        
        try:
            while True:
                # 检查是否需要停止搜索
                if not search_status['is_running']:
                    # 发送用户停止信号
                    stop_data = {
                        'type': 'stopped',
                        'content': {'message': '搜索已停止'}
                    }
                    yield f"data: {json.dumps(stop_data, ensure_ascii=False)}\n\n"
                    break
                
                # 从数据队列获取数据
                if not data_queue.empty():
                    data = data_queue.get()
                    
                    # 检查是否搜索结束
                    if data.get('type') == 'end':
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        # 发送剩余的Python日志
                        while not log_queue.empty():
                            log = log_queue.get()
                            yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
                        break
                    
                    # 发送数据
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                # 从日志队列获取并发送日志
                while not log_queue.empty():
                    log = log_queue.get()
                    yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
                
                # 短暂睡眠避免CPU占用过高
                time.sleep(0.05)
                
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