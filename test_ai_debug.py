#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI翻译调试脚本
"""

import logging
import sys
import os

# 设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_extractor import extract_info_with_ai

# 测试AI翻译功能
title = "The effects of vitamin D supplementation on immune function in elderly patients with chronic kidney disease"
abstract = "Background: Vitamin D deficiency is common in elderly patients with chronic kidney disease (CKD) and is associated with impaired immune function. Objective: To investigate the effects of vitamin D supplementation on immune function in elderly patients with CKD. Methods: A randomized controlled trial was conducted in 120 elderly patients with CKD stages 3-5. Patients were randomly assigned to receive either vitamin D supplementation (50,000 IU weekly) or placebo for 12 weeks. Results: Vitamin D supplementation significantly increased serum 25-hydroxyvitamin D levels (p < 0.001) and improved immune function parameters, including increased CD4+ T cells and decreased proinflammatory cytokines (p < 0.05). Conclusion: Vitamin D supplementation improves immune function in elderly patients with CKD."

print("📄 测试AI翻译功能")
print(f"原文标题: {title}")
print("=" * 80)

# 调用AI提取函数
try:
    result = extract_info_with_ai(abstract, title)
    print("✅ AI提取结果:")
    print(f"原文标题: {result.get('原文标题', '无')}")
    print(f"翻译标题: {result.get('翻译标题', '无')}")
    print(f"研究对象: {result.get('研究对象', '无')}")
    print(f"样本量: {result.get('样本量', '无')}")
    print(f"结论摘要: {result.get('结论摘要', '无')}")
except Exception as e:
    logger.error(f"❌ AI提取失败: {e}")
    import traceback
    traceback.print_exc()
