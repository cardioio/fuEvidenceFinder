// 全局变量
let isSearching = false;
let currentController = null; // 用于取消 fetch 请求
let currentKeyword = ''; // 当前搜索关键词

// DOM 元素
const searchBtn = document.getElementById('search-btn');
const searchBtnText = document.getElementById('search-btn-text');
const loadingSpinner = document.getElementById('loading-spinner');
const searchInput = document.getElementById('search-input');
const searchSection = document.getElementById('search-section');
const executionSection = document.getElementById('execution-section');
const logConsole = document.getElementById('log-console');
const resultsTbody = document.getElementById('results-tbody');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const resultCount = document.getElementById('result-count');
const stopBtn = document.getElementById('stop-btn');
const exportCsvBtn = document.getElementById('exportBtn');

// 模态窗相关DOM元素
const confirmModal = document.getElementById('confirm-modal');
const modalContent = document.getElementById('modal-content');
const modalKeywordDisplay = document.getElementById('modal-keyword-display');
const maxResultsInput = document.getElementById('max-results');
const enableFulltextCheckbox = document.getElementById('enable-fulltext');
const confirmBtn = document.getElementById('confirm-btn');
const cancelBtn = document.getElementById('cancel-btn');
const closeModalBtn = document.getElementById('close-modal');

// 事件监听器
searchBtn.addEventListener('click', startSearch);
searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        startSearch();
    }
});
stopBtn.addEventListener('click', stopSearch);

// 模态窗事件监听器
confirmBtn.addEventListener('click', confirmSearch);
cancelBtn.addEventListener('click', closeModal);
closeModalBtn.addEventListener('click', closeModal);
maxResultsInput.addEventListener('input', validateMaxResults);
maxResultsInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        confirmSearch();
    }
});
enableFulltextCheckbox.addEventListener('change', function() {
    if (this.checked) {
        addLog('已开启原文搜索模式', 'info');
    } else {
        addLog('已关闭原文搜索模式', 'warning');
    }
});

// CSV导出按钮事件监听器
const exportBtn = document.getElementById('exportBtn');
if (exportBtn) {
    exportBtn.addEventListener('click', exportToCSV);
}

// 开始搜索
function startSearch() {
    const keyword = searchInput.value.trim();
    if (!keyword) {
        addLog('⚠️ 请输入搜索关键词', 'warning');
        searchInput.focus();
        return;
    }
    
    if (isSearching) {
        addLog('⚠️ 搜索正在进行中，请等待完成后再试', 'warning');
        return;
    }
    
    // 显示二次确认模态窗
    showConfirmModal(keyword);
}

// 显示二次确认模态窗
function showConfirmModal(keyword) {
    currentKeyword = keyword;
    modalKeywordDisplay.textContent = keyword;
    validateMaxResults(); // 初始验证
    confirmModal.classList.remove('hidden');
    
    // 动画显示模态窗
    setTimeout(() => {
        modalContent.classList.remove('scale-95', 'opacity-0');
        modalContent.classList.add('scale-100', 'opacity-100');
    }, 10);
    
    // 聚焦到结果数量输入框
    setTimeout(() => {
        maxResultsInput.focus();
        maxResultsInput.select();
    }, 300);
    
    addLog(`准备搜索关键词: "${keyword}"`, 'info');
}

// 关闭模态窗
function closeModal() {
    modalContent.classList.remove('scale-100', 'opacity-100');
    modalContent.classList.add('scale-95', 'opacity-0');
    
    setTimeout(() => {
        confirmModal.classList.add('hidden');
        currentKeyword = '';
    }, 300);
}

// 验证最大结果数量输入
function validateMaxResults() {
    const value = parseInt(maxResultsInput.value);
    const min = parseInt(maxResultsInput.min);
    const max = parseInt(maxResultsInput.max);
    
    // 移除之前的验证样式
    maxResultsInput.classList.remove('input-error', 'input-success');
    
    if (isNaN(value) || value < min || value > max) {
        maxResultsInput.classList.add('input-error');
        confirmBtn.disabled = true;
        return false;
    } else {
        maxResultsInput.classList.add('input-success');
        confirmBtn.disabled = false;
        return true;
    }
}

// 添加输入验证提示
function addInputValidationTips() {
    // 实时提示建议数量
    maxResultsInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        let tipText = '';
        let tipClass = 'text-gray-500';
        
        if (isNaN(value)) {
            tipText = '请输入有效数字';
            tipClass = 'text-red-500';
        } else if (value < 10) {
            tipText = '⚠️ 结果较少，可能影响分析的全面性';
            tipClass = 'text-yellow-600';
        } else if (value > 50) {
            tipText = '⚠️ 结果较多，搜索时间可能较长';
            tipClass = 'text-yellow-600';
        } else {
            tipText = '✅ 推荐范围，分析效果最佳';
            tipClass = 'text-green-600';
        }
        
        // 更新提示文本（如果存在提示元素）
        let tipElement = document.getElementById('results-tip');
        if (!tipElement) {
            tipElement = document.createElement('p');
            tipElement.id = 'results-tip';
            tipElement.className = 'text-xs mt-1 transition-colors duration-200';
            maxResultsInput.parentNode.parentNode.appendChild(tipElement);
        }
        tipElement.textContent = tipText;
        tipElement.className = `text-xs mt-1 transition-colors duration-200 ${tipClass}`;
    });
}

// 增强状态反馈
function enhanceStatusFeedback() {
    // 搜索按钮状态反馈
    function updateSearchButtonState(searching, disabled = false) {
        if (disabled) {
            searchBtn.classList.add('opacity-50', 'cursor-not-allowed');
            searchBtn.disabled = true;
            return;
        }
        
        if (searching) {
            searchBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            searchBtn.disabled = true;
            searchBtnText.textContent = '搜索中...';
            loadingSpinner.classList.remove('hidden');
        } else {
            searchBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            searchBtn.disabled = false;
            searchBtnText.textContent = '搜索';
            loadingSpinner.classList.add('hidden');
        }
    }
    
    // 确认按钮状态反馈
    function updateConfirmButtonState(valid, processing = false) {
        if (processing) {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = `
                <div class="loading-spinner w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                处理中...
            `;
        } else {
            confirmBtn.disabled = !valid;
            confirmBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                开始搜索
            `;
        }
    }
    
    return { updateSearchButtonState, updateConfirmButtonState };
}

// 确认搜索
function confirmSearch() {
    if (!validateMaxResults()) {
        addLog('请输入有效的结果数量 (1-100)', 'error');
        return;
    }
    
    const maxResults = parseInt(maxResultsInput.value);
    const enableFulltext = enableFulltextCheckbox.checked;
    
    // 显示确认按钮处理状态
    const { updateConfirmButtonState } = enhanceStatusFeedback();
    updateConfirmButtonState(true, true);
    
    // 关闭模态窗
    closeModal();
    
    // 开始执行搜索
    executeSearch(currentKeyword, maxResults, enableFulltext);
}

// 执行搜索
function executeSearch(keyword, maxResults, enableFulltext) {
    if (isSearching) return;
    
    // 显示执行区域
    executionSection.classList.remove('hidden');
    searchSection.classList.add('hidden');
    
    // 重置界面
    clearLogs();
    clearResults();
    updateStatus('正在初始化...', 'loading');
    
    // 记录搜索配置
    addLog(`搜索配置 - 关键词: "${keyword}"`, 'info');
    addLog(`搜索配置 - 最大结果数: ${maxResults}篇`, 'info');
    addLog(`搜索配置 - 原文搜索: ${enableFulltext ? '开启' : '关闭'}`, 'info');
    
    // 开始搜索
    isSearching = true;
    updateSearchButton(true);
    startStreamSearch(keyword, maxResults, enableFulltext);
}

// 停止搜索
function stopSearch() {
    if (!isSearching) return;
    
    isSearching = false;
    updateSearchButton(false);
    updateStatus('进程已停止', 'stopped');
    
    // 更新停止按钮文本为重新搜索，并修改样式为绿色
    stopBtn.innerHTML = '🔄 重新搜索';
    stopBtn.className = 'bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm transition-colors';
    stopBtn.removeEventListener('click', stopSearch);
    stopBtn.addEventListener('click', restartSearch);
    
    // 取消 fetch 请求
    if (currentController) {
        currentController.abort();
        currentController = null;
    }
    
    addLog('用户停止了搜索', 'warning');
}

// 重新搜索
function restartSearch() {
    // 重置搜索输入框为空状态
    searchInput.value = '';
    
    // 重置搜索参数
    document.getElementById('max-results').value = '20';
    document.getElementById('enable-fulltext').checked = true;
    
    // 切换界面区域：隐藏执行区域，显示搜索区域
    executionSection.classList.add('hidden');
    searchSection.classList.remove('hidden');
    
    // 重置UI状态
    updateStatus('准备就绪', 'ready');
    
    // 重置按钮文本和样式
    stopBtn.innerHTML = '🛑 停止搜索';
    stopBtn.className = 'bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm transition-colors';
    stopBtn.removeEventListener('click', restartSearch);
    stopBtn.addEventListener('click', stopSearch);
    
    // 清空搜索结果和日志
    clearResults();
    clearLogs();
    
    // 页面滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    addLog('准备开始新的搜索', 'info');
    
    // 聚焦到搜索输入框，提供良好的用户体验
    setTimeout(() => {
        searchInput.focus();
    }, 100);
}

// 开始流式搜索
function startStreamSearch(keyword, maxResults = 20, enableFulltext = true) {
    const url = `http://localhost:5001/stream_search?keyword=${encodeURIComponent(keyword)}&max_results=${maxResults}&enable_fulltext=${enableFulltext}`;
    
    // 创建 AbortController 用于取消请求
    currentController = new AbortController();
    
    // 使用 fetch API 接收流数据
    fetch(url, { signal: currentController.signal })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            // 状态计数器
            let processedResults = 0;
            
            function processData() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        console.log('流数据读取完成');
                        isSearching = false;
                        updateSearchButton(false);
                        updateStatus('搜索完成', 'completed');
                        addLog(`搜索完成，共获取 ${processedResults} 条结果`, 'success');
                        
                        // 更新停止按钮为重新搜索状态
                        const stopBtn = document.getElementById('stop-btn');
                        stopBtn.innerHTML = '🔄 重新搜索';
                        stopBtn.className = 'bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm transition-colors';
                        stopBtn.removeEventListener('click', stopSearch);
                        stopBtn.addEventListener('click', restartSearch);
                        
                        return;
                    }
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop(); // 保存不完整的行
                    
                    lines.forEach(line => {
                        line = line.trim();
                        if (line.startsWith('data: ')) {
                            try {
                                const jsonStr = line.substring(6); // 移除 'data: ' 前缀
                                const data = JSON.parse(jsonStr);
                                
                                if (!isSearching) return;
                                
                                if (data.type === 'log' && data.content) {
                                    // 处理日志消息
                                    const { timestamp, level, message } = data.content;
                                    addLog(message, level);
                                    
                                    // 更新状态指示器
                                    if (message.includes('开始搜索')) {
                                        updateStatus('正在搜索中...', 'running');
                                    } else if (message.includes('完成')) {
                                        updateStatus('搜索完成', 'completed');
                                    }
                                    
                                } else if (data.type === 'row' && data.content) {
                                    // 处理数据行
                                    addResultRow(data.content);
                                    processedResults++;
                                    resultCount.textContent = `结果: ${processedResults}`;
                                    
                                } else if (data.type === 'end') {
                                    isSearching = false;
                                    updateSearchButton(false);
                                    updateStatus('搜索完成', 'completed');
                                    addLog(`搜索完成，共获取 ${processedResults} 条结果`, 'success');
                                    
                                    // 更新导出按钮状态（如果有结果）
                                    updateExportButtonState(processedResults > 0);
                                    
                                    // 更新停止按钮为重新搜索状态
                                    const stopBtn = document.getElementById('stop-btn');
                                    stopBtn.innerHTML = '🔄 重新搜索';
                                    stopBtn.className = 'bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm transition-colors';
                                    stopBtn.removeEventListener('click', stopSearch);
                                    stopBtn.addEventListener('click', restartSearch);
                                } else if (data.type === 'stopped') {
                                    isSearching = false;
                                    updateSearchButton(false);
                                    updateStatus('搜索已停止', 'stopped');
                                    addLog(`搜索已停止，已获取 ${processedResults} 条结果`, 'warning');
                                    
                                    // 更新导出按钮状态（如果有结果）
                                    updateExportButtonState(processedResults > 0);
                                }
                            } catch (parseError) {
                                console.error('解析数据出错:', parseError, '原始数据:', line);
                            }
                        }
                    });
                    
                    if (isSearching) {
                        processData();
                    }
                });
            }
            
            processData();
        })
        .catch(error => {
            console.error('流式搜索错误:', error);
            isSearching = false;
            updateSearchButton(false);
            updateStatus('搜索失败: ' + error.message, 'error');
            addLog('搜索请求失败: ' + error.message, 'error');
        });
}

// 更新搜索按钮状态
function updateSearchButton(searching) {
    if (searching) {
        searchBtn.disabled = true;
        searchBtnText.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
    } else {
        searchBtn.disabled = false;
        searchBtnText.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
    }
}

// 更新状态
function updateStatus(text, type) {
    statusText.textContent = text;
    
    // 更新状态指示器
    statusIndicator.className = 'w-3 h-3 rounded-full';
    switch (type) {
        case 'loading':
        case 'running':
            statusIndicator.classList.add('bg-yellow-500', 'animate-pulse');
            break;
        case 'completed':
            statusIndicator.classList.add('bg-green-500');
            break;
        case 'stopped':
        case 'error':
            statusIndicator.classList.add('bg-red-500');
            break;
        default:
            statusIndicator.classList.add('bg-green-500');
    }
}

// 添加日志
function addLog(message, level = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry flex items-start space-x-3 text-sm';
    
    // 根据日志级别设置颜色
    let colorClass = 'text-green-400';
    if (level === 'warning') colorClass = 'text-yellow-400';
    if (level === 'error' || level === 'danger') colorClass = 'text-red-400';
    if (level === 'success') colorClass = 'text-green-300';
    
    logEntry.innerHTML = `
        <span class="text-gray-500 text-xs mt-0.5">${timestamp}</span>
        <span class="${colorClass}">${message}</span>
    `;
    
    logConsole.appendChild(logEntry);
    logConsole.scrollTop = logConsole.scrollHeight;
}

// CSV导出功能
function exportToCSV() {
    const table = document.getElementById('results-table');
    const rows = table.querySelectorAll('tbody tr');
    
    // 检查是否有数据可导出
    if (rows.length === 0 || (rows.length === 1 && rows[0].querySelector('td[colspan]'))) {
        addLog('⚠️ 暂无搜索结果可供导出', 'warning');
        return;
    }
    
    // 定义列标题（按表格显示顺序）
    const headers = [
        '发表年份',
        '数据收集年份', 
        '国家',
        '研究类型',
        '研究对象',
        '样本量',
        '推荐补充剂量',
        '作用机理',
        '证据等级',
        '结论摘要',
        '标题',
        'PMID',
        '全文状态'
    ];
    
    // 准备CSV数据
    const csvData = [];
    
    // 添加表头
    csvData.push(headers);
    
    // 添加数据行
    rows.forEach(row => {
        // 跳过空状态行
        if (row.querySelector('td[colspan]')) return;
        
        const cells = row.querySelectorAll('td');
        if (cells.length >= 13) {
            const rowData = [];
            
            // 按照定义的列顺序提取数据
            for (let i = 0; i < 13; i++) {
                let cellContent = cells[i].textContent.trim();
                
                // 处理PMID链接 - 只提取PMID数字
                if (i === 11) { // PMID列（从0开始）
                    const linkElement = cells[i].querySelector('a');
                    if (linkElement) {
                        cellContent = linkElement.textContent.trim();
                    }
                }
                
                // 清理并转义特殊字符
                cellContent = cellContent.replace(/\s+/g, ' ').trim();
                if (cellContent === '-') cellContent = '';
                
                // 转义CSV特殊字符（引号、逗号、换行符）
                if (cellContent.includes('"') || cellContent.includes(',') || cellContent.includes('\n') || cellContent.includes('\r')) {
                    cellContent = '"' + cellContent.replace(/"/g, '""') + '"';
                }
                
                rowData.push(cellContent);
            }
            
            csvData.push(rowData);
        }
    });
    
    // 生成CSV内容
    const csvContent = csvData.map(row => row.join(',')).join('\n');
    
    // 添加BOM以支持中文显示
    const bom = new Uint8Array([0xEF, 0xBB, 0xBF]);
    const blob = new Blob([bom, csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // 生成文件名（包含当前日期时间）
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    const keyword = currentKeyword ? currentKeyword.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_') : 'search_results';
    const filename = `文献搜索结果_${keyword}_${year}${month}${day}_${hours}${minutes}${seconds}.csv`;
    
    // 下载文件
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    addLog(`✅ CSV文件导出成功: ${filename}`, 'success');
}

// 更新导出按钮状态
function updateExportButtonState(hasData) {
    if (exportCsvBtn) {
        exportCsvBtn.disabled = !hasData;
        if (hasData) {
            exportCsvBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            exportCsvBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }
}

// 清空日志
function clearLogs() {
    logConsole.innerHTML = '<div class="text-gray-500 text-center pt-8">等待搜索开始...</div>';
}

// 清空结果
function clearResults() {
    resultsTbody.innerHTML = `
        <tr>
            <td colspan="14" class="px-6 py-8 text-center text-gray-500">
                暂无搜索结果
            </td>
        </tr>
    `;
    updateExportButtonState(false); // 更新导出按钮状态
}

// 添加单行结果
function addResultRow(result) {
    // 如果是第一行结果，清空"暂无搜索结果"提示
    const emptyRow = resultsTbody.querySelector('tr td[colspan="14"]');
    if (emptyRow) {
        resultsTbody.innerHTML = '';
    }
    
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50 transition-colors opacity-0';
    
    // 处理可能为空的字段
    const publishedYear = result.发表年份 || '-';
    const dataCollectionYear = result.数据收集年份 || '-';
    const country = result.国家 || '-';
    const studyType = result.研究类型 || '-';
    const studySubject = result.研究对象 || '-';
    const sampleSize = result.样本量 || '-';
    const recommendedDose = result['推荐补充剂量/用法'] || '-';
    const mechanism = result.作用机理 || '-';
    const evidenceLevel = result.证据等级 || '-';
    const conclusion = result.结论摘要 || '-';
    const title = result.标题 || result.原文标题 || '-';
    const translatedTitle = result.翻译标题 || '-';
    const pmid = result.PMID || '-';
    const fulltextStatus = result.免费全文状态 || '-';
    const fulltextLinks = result.免费全文链接数 || '-';
    const extractionStatus = result.全文提取状态 || '-';
    const abstractContent = result.摘要主要内容 || '-';
    const fulltextSummary = result.全文内容摘要 || '-';
    
    // 截断长文本以保持表格美观
    const truncateText = (text, maxLength = 50) => {
        if (!text || text === '-') return '-';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // 格式化全文状态显示
    const getStatusBadge = (status) => {
        if (!status || status === '-') return '<span class="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">-</span>';
        if (status === '可用') return '<span class="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">可用</span>';
        if (status === '已提取') return '<span class="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">已提取</span>';
        if (status === '提取中') return '<span class="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">提取中</span>';
        return `<span class="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">${status}</span>`;
    };
    
    // 格式化PMID链接
    const getPMIDLink = (pmid) => {
        if (!pmid || pmid === '-') return '-';
        return `<a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}" target="_blank" class="text-blue-600 hover:text-blue-800 underline transition-colors">${pmid}</a>`;
    };

    // 格式化全文状态显示为免费/付费
    const getFulltextStatusText = (status) => {
        if (!status || status === '-') return '-';
        if (status === '可用' || status === '免费') return '免费';
        if (status === '付费' || status === '需要订阅') return '付费';
        if (status === '提取中' || status === '已提取') return '免费'; // 已提取的认为免费
        return status.includes('免费') ? '免费' : '付费';
    };

    row.innerHTML = `
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[80px]">${publishedYear}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[100px]">${dataCollectionYear}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[90px]">${country}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[100px]">${studyType}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[120px]">${studySubject}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[80px]">${sampleSize}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[180px] max-w-[250px]">
            <div class="break-words" title="${recommendedDose}">${recommendedDose}</div>
        </td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[180px] max-w-[250px]">
            <div class="break-words" title="${mechanism}">${mechanism}</div>
        </td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[90px]">${evidenceLevel}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[200px] max-w-[300px]">
            <div class="break-words" title="${conclusion}">${conclusion}</div>
        </td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[200px] max-w-[300px]">
            <div class="break-words" title="${title}">${title}</div>
        </td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[200px] max-w-[300px]">
            <div class="break-words" title="${translatedTitle}">${translatedTitle}</div>
        </td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[100px]">${getPMIDLink(pmid)}</td>
        <td class="px-3 py-4 text-xs text-gray-900 align-top min-w-[100px]">
            <span class="px-2 py-1 rounded-full text-xs font-medium ${getFulltextStatusText(fulltextStatus) === '免费' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                ${getFulltextStatusText(fulltextStatus)}
            </span>
        </td>
    `;
    
    resultsTbody.appendChild(row);
    
    // 动画显示新行
    setTimeout(() => {
        row.style.transition = 'opacity 0.3s ease';
        row.classList.remove('opacity-0');
    }, 10);
    
    // 更新导出按钮状态（如果有数据）
    updateExportButtonState(true);
}

// 显示结果（兼容性函数）
function displayResults(results) {
    if (!results || results.length === 0) {
        clearResults();
        return;
    }
    
    clearResults();
    results.forEach(result => {
        addResultRow(result);
    });
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('📚 文献检索系统已加载');
    
    // 初始化输入验证提示
    addInputValidationTips();
    
    // 焦点到搜索框
    searchInput.focus();
});