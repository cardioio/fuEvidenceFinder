#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证AI提取功能是否正确返回翻译后的标题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from pubmed import parse_record
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_translation():
    """测试AI翻译标题功能"""
    print("=== 测试AI翻译标题功能 ===")
    
    # 创建一个模拟的完整article对象
    mock_article = {
        'MedlineCitation': {
            'PMID': '37542189',
            'Article': {
                'ArticleTitle': 'The effects of vitamin D supplementation on immune function in elderly patients with chronic kidney disease',
                'Abstract': {
                    'AbstractText': 'Background: Vitamin D deficiency is common in elderly patients with chronic kidney disease (CKD). The aim of this study was to evaluate the effects of vitamin D supplementation on immune function in elderly patients with CKD. Methods: A randomized controlled trial was conducted in 120 elderly CKD patients. Patients were randomly assigned to receive either vitamin D supplementation (n=60) or placebo (n=60) for 12 months. Immune function parameters including CD4+ T cells, CD8+ T cells, and natural killer cells were measured at baseline and after 12 months of treatment. Results: Vitamin D supplementation significantly increased CD4+ T cell counts (p<0.05) and improved the CD4+/CD8+ ratio (p<0.05) compared to placebo. Conclusion: Vitamin D supplementation may improve immune function in elderly patients with CKD.'
                },
                'AuthorList': {
                    'Author': [
                        {'ForeName': 'John', 'LastName': 'Doe', 'Affiliation': 'Department of Nephrology, University of California, San Francisco, CA, USA'},
                        {'ForeName': 'Jane', 'LastName': 'Smith', 'Affiliation': 'Department of Nutrition, Stanford University, Stanford, CA, USA'}
                    ]
                },
                'Journal': {
                    'JournalIssue': {
                        'PubDate': {
                            'Year': '2023'
                        }
                    }
                },
                'PublicationTypeList': ['Randomized Controlled Trial', 'Journal Article']
            },
            'MedlineJournalInfo': {
                'Country': 'United States'
            }
        }
    }
    
    # 调用parse_record函数测试
    try:
        # 禁用全文提取以加快测试
        data = parse_record(mock_article, enable_fulltext=False)
        
        print("✅ 测试完成")
        print(f"📄 原文标题: {data.get('原文标题')}")
        print(f"🌐 翻译标题: {data.get('翻译标题')}")
        
        # 检查翻译标题是否有效
        if data.get('翻译标题') and data.get('翻译标题') != "翻译失败":
            print("🎉 翻译标题提取成功！")
            return True
        else:
            print("❌ 翻译标题提取失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        logger.error(f"测试出错: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    test_translation()
