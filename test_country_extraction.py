#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的国家信息提取功能

测试内容包括：
1. 新的国家信息提取函数 extract_country_from_affiliation
2. AI提示词中的国家字段提取
3. 过滤城市、邮政编码、机构名称等无效信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pubmed import extract_country_from_affiliation, extract_info_with_ai
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_country_extraction_function():
    """
    测试新的国家信息提取函数
    """
    print("\n=== 测试国家信息提取函数 ===")
    
    # 测试案例：包含各种机构信息的文章数据
    test_cases = [
        # 案例1：包含邮政编码的加拿大机构
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Department of Nutrition, McGill University, 21111 Lakeshore Road, Ste-Anne-de-Bellevue, Quebec, Canada H9X 3V9"
                }]
            }],
            "expected": "Canada",
            "description": "加拿大机构（含邮政编码）"
        },
        
        # 案例2：美国机构
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Department of Medicine, University of Colorado Anschutz Medical Campus, Aurora, CO, USA"
                }]
            }],
            "expected": "United States",
            "description": "美国机构"
        },
        
        # 案例3：包含城市的中国机构
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "School of Public Health, Shanghai Jiao Tong University, Shanghai, China"
                }]
            }],
            "expected": "China",
            "description": "中国机构（含城市名）"
        },
        
        # 案例4：英国机构
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Institute of Food Research, Norwich Research Park, Norwich, NR4 7UA, United Kingdom"
                }]
            }],
            "expected": "United Kingdom",
            "description": "英国机构"
        },
        
        # 案例5：德国机构
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Institute of Nutrition, University of Bonn, Germany"
                }]
            }],
            "expected": "Germany",
            "description": "德国机构"
        },
        
        # 案例6：包含街道地址的澳大利亚机构
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "School of Nutrition and Dietetics, Deakin University, 221 Burwood Highway, Melbourne, Australia"
                }]
            }],
            "expected": "Australia",
            "description": "澳大利亚机构（含街道地址）"
        },
        
        # 案例7：应该被过滤的无效信息（纯城市名）
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "Department of Internal Medicine, Denver, Colorado"
                }]
            }],
            "expected": "需人工确认",
            "description": "纯城市信息（应被过滤）"
        },
        
        # 案例8：应该被过滤的邮政编码
        {
            "AuthorList": [{
                "AffiliationInfo": [{
                    "Affiliation": "H9X 3V9, Canada"
                }]
            }],
            "expected": "Canada",
            "description": "以邮政编码开头"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        try:
            result = extract_country_from_affiliation(case)
            status = "✅ PASS" if result == case["expected"] else "❌ FAIL"
            
            if result == case["expected"]:
                passed += 1
                
            print(f"\n测试 {i}: {case['description']}")
            print(f"  输入: {case['AuthorList'][0]['AffiliationInfo'][0]['Affiliation'][:80]}...")
            print(f"  期望: {case['expected']}")
            print(f"  结果: {result}")
            print(f"  状态: {status}")
            
        except Exception as e:
            print(f"\n测试 {i}: {case['description']}")
            print(f"  错误: {e}")
            print(f"  状态: ❌ ERROR")
    
    print(f"\n=== 国家提取函数测试完成 ===")
    print(f"通过: {passed}/{total} ({passed/total*100:.1f}%)")
    return passed, total

def test_ai_country_extraction():
    """
    测试AI提示词中的国家信息提取
    """
    print("\n=== 测试AI国家信息提取 ===")
    
    # 包含不同国家信息的测试摘要
    test_abstracts = [
        {
            "text": """This randomized controlled trial was conducted at the University of California, San Francisco, USA. 
            We enrolled 120 overweight adults (BMI 25-30) aged 25-55 years. Participants received 30ml MCT oil daily for 12 weeks. 
            Results showed significant reductions in body fat mass.""",
            "expected_country": "美国",
            "description": "美国研究摘要"
        },
        
        {
            "text": """A multicenter study was performed at three hospitals in Beijing and Shanghai, China. 
            We investigated the effects of MCT supplementation on 80 Chinese participants with metabolic syndrome. 
            The study was conducted between 2020-2022.""",
            "expected_country": "中国",
            "description": "中国研究摘要"
        },
        
        {
            "text": """This research was conducted at the Department of Nutrition, University of Toronto, Canada. 
            We studied MCT effects on 60 Canadian adults in a controlled trial. 
            The study took place in Toronto, Ontario.""",
            "expected_country": "加拿大",
            "description": "加拿大研究摘要（包含城市名Toronto应被过滤）"
        },
        
        {
            "text": """A crossover study was performed at Imperial College London, United Kingdom. 
            We examined MCT supplementation effects on 40 healthy volunteers in London. 
            The research was funded by UK Medical Research Council.""",
            "expected_country": "英国",
            "description": "英国研究摘要"
        },
        
        {
            "text": """This clinical trial was conducted at the German Diabetes Center, Düsseldorf, Germany. 
            We investigated MCT oil effects on 100 German participants with type 2 diabetes. 
            The study duration was 16 weeks.""",
            "expected_country": "德国",
            "description": "德国研究摘要"
        },
        
        {
            "text": """A pilot study was performed without clear geographic information. 
            The research involved MCT supplementation effects on metabolic parameters. 
            No specific country was mentioned in the abstract.""",
            "expected_country": "未明确说明",
            "description": "无明确国家信息的摘要"
        }
    ]
    
    passed = 0
    total = len(test_abstracts)
    
    for i, case in enumerate(test_abstracts, 1):
        try:
            print(f"\n测试 {i}: {case['description']}")
            print(f"  摘要: {case['text'][:100]}...")
            
            # 调用AI提取函数
            result = extract_info_with_ai(case["text"])
            extracted_country = result.get("国家", "N/A")
            
            status = "✅ PASS" if extracted_country == case["expected_country"] else "❌ FAIL"
            
            if extracted_country == case["expected_country"]:
                passed += 1
                
            print(f"  期望国家: {case['expected_country']}")
            print(f"  提取国家: {extracted_country}")
            print(f"  其他字段:")
            for key, value in result.items():
                if key != "国家":
                    print(f"    {key}: {value}")
            print(f"  状态: {status}")
            
        except Exception as e:
            print(f"\n测试 {i}: {case['description']}")
            print(f"  错误: {e}")
            print(f"  状态: ❌ ERROR")
    
    print(f"\n=== AI国家信息提取测试完成 ===")
    print(f"通过: {passed}/{total} ({passed/total*100:.1f}%)")
    return passed, total

def main():
    """
    主测试函数
    """
    print("开始测试改进后的国家信息提取功能...")
    
    # 测试1：国家提取函数
    func_passed, func_total = test_country_extraction_function()
    
    # 测试2：AI国家信息提取
    ai_passed, ai_total = test_ai_country_extraction()
    
    # 总体结果
    total_passed = func_passed + ai_passed
    total_tests = func_total + ai_total
    
    print(f"\n" + "="*60)
    print(f"测试总结:")
    print(f"  国家提取函数: {func_passed}/{func_total} ({func_passed/func_total*100:.1f}%)")
    print(f"  AI国家信息提取: {ai_passed}/{ai_total} ({ai_passed/ai_total*100:.1f}%)")
    print(f"  总计: {total_passed}/{total_tests} ({total_passed/total_tests*100:.1f}%)")
    
    if total_passed == total_tests:
        print("🎉 所有测试通过！国家信息提取功能工作正常。")
    else:
        print("⚠️  部分测试失败，请检查相关功能。")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)