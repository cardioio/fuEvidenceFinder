#!/usr/bin/env python3
"""
调试国家提取函数的简单脚本
"""

from pubmed import extract_country_from_affiliation
import logging

# 配置详细日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加拿大测试案例
test_data = {
    "AuthorList": [{
        "AffiliationInfo": [{
            "Affiliation": "Department of Nutrition, McGill University, 21111 Lakeshore Road, Ste-Anne-de-Bellevue, Quebec, Canada H9X 3V9"
        }]
    }]
}

print("=== 调试国家提取函数 ===")
print(f"测试数据: {test_data}")
print(f"调用函数...")

result = extract_country_from_affiliation(test_data)
print(f"提取结果: {result}")