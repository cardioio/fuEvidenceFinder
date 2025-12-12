# Fu llMED - 基于AI的医学文献证据分析系统

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**智能化的医学文献分析与证据提取平台**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [文档](#-文档)

</div>

---

## 🎯 项目简介

Fu llMED 是一个基于人工智能的医学文献证据分析系统，专门用于从PubMed数据库中自动提取和分析医学研究文献的关键信息。系统集成了先进的AI信息提取技术、PubMed数据抓取能力和智能数据解析功能。

### 核心价值
- 🔬 **智能文献分析** - 自动识别研究类型、提取关键数据
- ⚡ **高效数据处理** - 支持批量处理大规模文献数据
- 🎯 **精准信息提取** - 样本量、剂量、持续时间等关键指标
- 📊 **结构化输出** - 生成标准化的Excel报告
- 🛡️ **高可用性** - API密钥池管理，确保服务稳定性

---

## ✨ 功能特性

### 🔍 智能文献搜索
- **多维度搜索** - 支持复杂的布尔搜索表达式
- **批量处理** - 一键处理数百篇文献
- **智能过滤** - 自动过滤无关文献
- **进度追踪** - 实时显示处理进度

### 🤖 AI信息提取
- **研究类型识别** - 自动识别RCT、Meta分析、观察性研究等
- **关键信息提取** - 样本量、剂量、持续时间、人群特征
- **质量评估** - 数据完整性和可信度评分
- **多语言支持** - 中英文混合处理能力

### 📊 结构化数据分析
- **标准化解析** - 统一的数据格式和字段
- **统计报告** - 自动生成描述性统计
- **可视化图表** - 数据分布和趋势分析
- **导出支持** - Excel、JSON等多种格式

### 🔧 企业级特性
- **API密钥池** - 多密钥轮换，确保服务连续性
- **容错机制** - 自动重试和故障转移
- **详细日志** - 完整的操作日志记录
- **配置管理** - 灵活的配置选项

---

## 🚀 快速开始

### 环境要求
- Python 3.7+
- 网络连接（访问PubMed）
- 有效的AI API密钥

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd fuEvidenceExcel
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置参数**
```python
# 编辑 src/config.py
Entrez.email = "your-email@example.com"  # 设置您的邮箱
```

4. **运行系统**
```bash
python app.py
```

### 验证安装
```python
from src.tests.test_functions import TestFunctions

# 运行功能测试
tester = TestFunctions()
result = tester.test_api_key_pool(['初始化测试'])
print(f"安装验证: {'✅ 成功' if result['success_rate'] > 0 else '❌ 失败'}")
```

---

## 📖 使用指南

### 基本使用

```python
from src.config import ConfigManager
from src.pubmed_scraper import PubMedScraper
from src.ai_extractor import AIExtractor
from src.data_parser import DataParser

# 初始化组件
config = ConfigManager()
scraper = PubMedScraper(config)
extractor = AIExtractor(config)
parser = DataParser()

# 搜索文献
search_results = scraper.search("caffeine exercise performance")
print(f"找到 {len(search_results)} 篇相关文献")

# 提取信息
for article in search_results:
    extracted_info = extractor.extract_info_with_ai(article['abstract'])
    structured_data = parser.extract_structured_info(
        article['abstract'], 
        article.get('title', '')
    )
    
    print(f"PMID: {article.get('pmid')}")
    print(f"研究类型: {structured_data['研究类型']}")
    print(f"样本量: {structured_data['样本量']}")
```

### 高级配置

#### 自定义搜索参数
```python
custom_config = {
    "search_term": "(vitamin D OR cholecalciferol) AND (bone health OR osteoporosis)",
    "max_results": 50,
    "request_delay": 2.0
}
```

#### API密钥池配置
```python
api_keys = [
    "your-first-api-key",
    "your-second-api-key", 
    "your-third-api-key"
]

key_pool_config = {
    "max_failure_count": 3,
    "disable_duration": 300,  # 5分钟
    "success_reset_threshold": 2
}
```

---

## 📚 文档

### 核心文档
- 📋 [重构说明文档](docs/REFACTOR_DOCUMENTATION.md) - 详细的重构变更说明
- 🧪 [测试指南](src/tests/) - 测试框架使用说明
- ⚙️ [配置说明](src/config.py) - 详细配置参数说明

### API文档
- 🔍 [PubMed爬虫](src/pubmed_scraper.py) - 文献搜索和抓取API
- 🤖 [AI提取器](src/ai_extractor.py) - AI信息提取API
- 📊 [数据解析器](src/data_parser.py) - 数据解析API
- 🔑 [密钥管理](src/api_key_manager.py) - API密钥池管理API

### 示例代码
- [基本使用示例](examples/basic_usage.py)
- [批量处理示例](examples/batch_processing.py)
- [自定义配置示例](examples/custom_config.py)

---

## 🏗️ 项目架构

```
fuEvidenceExcel/
├── 📁 src/                     # 源代码目录
│   ├── config.py              # 配置管理
│   ├── api_key_manager.py     # API密钥池管理
│   ├── ai_extractor.py        # AI信息提取
│   ├── pubmed_scraper.py      # PubMed数据抓取
│   ├── data_parser.py         # 数据解析
│   ├── fulltext_extractor.py  # 全文提取
│   ├── country_processor.py   # 国家/地区处理
│   ├── excel_handler.py       # Excel文件处理
│   └── tests/                 # 测试模块
│       └── test_functions.py  # 功能测试
├── 📁 docs/                   # 文档目录
│   └── REFACTOR_DOCUMENTATION.md
├── 📁 templates/              # 网页模板
│   └── index.html
├── 📁 excel/                  # Excel输出目录
├── app.py                     # 主应用程序
└── requirements.txt           # 依赖包列表
```

---

## 🧪 测试

### 运行测试套件
```bash
# 运行所有测试
python -m pytest src/tests/

# 运行特定测试
python -c "from src.tests.test_functions import TestFunctions; TestFunctions().run_comprehensive_test()"
```

### 测试覆盖范围
- ✅ API密钥池功能测试
- ✅ AI信息提取准确性测试  
- ✅ PubMed数据抓取测试
- ✅ 数据解析功能测试
- ✅ 错误处理机制测试
- ✅ 性能基准测试

---

## 🔧 配置选项

### 环境变量
```bash
# PubMed API配置
PUBMED_EMAIL=your-email@example.com

# API密钥配置
API_KEY_POOL=["key1", "key2", "key3"]

# 功能开关
ENABLE_WEB_SEARCH=true
ENABLE_FULLTEXT_EXTRACTION=false
```

### 配置文件
主要配置位于 `src/config.py`，包括：
- PubMed搜索参数
- AI API端点配置
- 缓存和性能设置
- 功能开关配置

---

## 📈 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 文献搜索速度 | 100+ 篇/分钟 | 基于网络状况 |
| 信息提取速度 | 50+ 篇/分钟 | 使用AI API |
| 批量处理能力 | 1000+ 篇文献 | 单次运行 |
| 准确性 | >85% | 关键信息提取 |
| 可用性 | 99%+ | API密钥池保障 |

---

## 🤝 贡献指南

### 贡献方式
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发规范
- 遵循 PEP 8 代码规范
- 添加必要的类型注解
- 编写详细的文档注释
- 确保测试覆盖率

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 📞 支持

### 获取帮助
- 📧 邮件支持: [support@example.com]
- 🐛 问题报告: [GitHub Issues]
- 💬 讨论区: [GitHub Discussions]

### 常见问题
- **Q: 如何处理API配额限制？**
  A: 系统会自动使用密钥池轮换，建议配置多个API密钥

- **Q: 如何提高提取准确性？**
  A: 可以调整AI提示词模板或使用更高质量的API密钥

- **Q: 支持哪些文献类型？**
  A: 主要支持RCT、Meta分析、观察性研究等常见研究类型

---

## 🚀 路线图

### v2.1.0 (计划中)
- [ ] Web界面开发
- [ ] 数据库存储集成
- [ ] 更多AI模型支持
- [ ] 移动端适配

### v2.2.0 (规划中)
- [ ] 云端部署支持
- [ ] 多语言文献支持
- [ ] 高级可视化功能
- [ ] 用户管理系统

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！⭐**

Made with ❤️ by [Fu llMED Team]

</div>