#!/usr/bin/env python3

from pubmed import extract_country_from_affiliation
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 澳大利亚测试案例
test_data = {
    "AuthorList": [{
        "AffiliationInfo": [{
            "Affiliation": "School of Nutrition and Dietetics, Deakin University, 221 Burwood Highway, Melbourne, Australia"
        }]
    }]
}

print("=== 调试澳大利亚测试案例 ===")
result = extract_country_from_affiliation(test_data)
print(f"提取结果: {result}")

# 科罗拉多州测试案例
test_data2 = {
    "AuthorList": [{
        "AffiliationInfo": [{
            "Affiliation": "Department of Internal Medicine, Denver, Colorado"
        }]
    }]
}

print("\n=== 调试科罗拉多州测试案例 ===")
result2 = extract_country_from_affiliation(test_data2)
print(f"提取结果: {result2}")