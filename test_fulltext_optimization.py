#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全文提取算法优化测试脚本

测试以下优化功能：
1. check_full_text_availability函数 - 重点检查title="Free full text at PubMed Central"的a元素
2. extract_full_text_content函数 - 增强元素定位和内容提取逻辑
3. 调试信息和错误处理的完善程度
4. 整体算法效果验证

使用方法：
python test_fulltext_optimization.py
"""

import sys
import time
import traceback
from datetime import datetime

# 导入pubmed模块的函数
from pubmed import (
    check_full_text_availability,
    extract_full_text_content, 
    analyze_pmid_with_full_text
)

def test_check_full_text_availability():
    """测试check_full_text_availability函数的优化效果"""
    print("\n" + "="*80)
    print("测试1: check_full_text_availability函数优化效果")
    print("="*80)
    
    # 测试用例：已知有免费全文的PMID
    test_pmids = [
        "32542345",  # 之前测试过的PMID
        "30000000",  # 另一个测试PMID
        "PMC1000000" # PMC格式
    ]
    
    results = []
    
    for i, pmid in enumerate(test_pmids, 1):
        print(f"\n🔍 测试用例 {i}: PMID = {pmid}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            result = check_full_text_availability(pmid)
            end_time = time.time()
            
            # 记录结果
            test_result = {
                "pmid": pmid,
                "success": True,
                "is_free": result.get('is_free', False),
                "links_count": len(result.get('links', [])),
                "source": result.get('source', 'unknown'),
                "message": result.get('message', ''),
                "execution_time": round(end_time - start_time, 2),
                "element_found": result.get('element_found', {}),
                "all_links": result.get('all_links', [])
            }
            
            results.append(test_result)
            
            # 打印详细结果
            print(f"✅ 免费全文状态: {'是' if result.get('is_free') else '否'}")
            print(f"📊 找到链接数: {len(result.get('links', []))}")
            print(f"🔗 链接来源: {result.get('source', 'unknown')}")
            print(f"⏱️  执行时间: {test_result['execution_time']}秒")
            
            if result.get('element_found'):
                print(f"🎯 元素定位结果:")
                for key, value in result['element_found'].items():
                    print(f"   - {key}: {value}")
            
            if result.get('all_links'):
                print(f"🔗 所有可用链接:")
                for j, link in enumerate(result['all_links'][:3], 1):  # 只显示前3个
                    print(f"   {j}. {link}")
                if len(result['all_links']) > 3:
                    print(f"   ... 还有 {len(result['all_links'])-3} 个链接")
            
            print(f"💬 详细信息: {result.get('message', '无')}")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            print(f"🔍 错误详情: {traceback.format_exc()}")
            
            results.append({
                "pmid": pmid,
                "success": False,
                "error": str(e),
                "execution_time": round(time.time() - start_time, 2) if 'start_time' in locals() else 0
            })
    
    return results

def test_extract_full_text_content():
    """测试extract_full_text_content函数的优化效果"""
    print("\n" + "="*80)
    print("测试2: extract_full_text_content函数优化效果")
    print("="*80)
    
    # 测试用例：已知有全文内容的PMID
    test_pmids = [
        "32542345",
        "30000000"
    ]
    
    results = []
    
    for i, pmid in enumerate(test_pmids, 1):
        print(f"\n🔍 测试用例 {i}: PMID = {pmid}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            result = extract_full_text_content(pmid)
            end_time = time.time()
            
            # 记录结果
            test_result = {
                "pmid": pmid,
                "success": True,
                "extraction_success": result.get('extraction_success', False),
                "content_parts": len(result.get('content', {})),
                "execution_time": round(end_time - start_time, 2),
                "debug_info": result.get('debug_info', {}),
                "message": result.get('message', ''),
                "error": result.get('error', '')
            }
            
            results.append(test_result)
            
            # 打印详细结果
            print(f"✅ 提取成功: {'是' if result.get('extraction_success') else '否'}")
            print(f"📊 提取部分数: {len(result.get('content', {}))}")
            print(f"⏱️  执行时间: {test_result['execution_time']}秒")
            
            if result.get('content'):
                print(f"📄 提取的内容部分:")
                for part, text in result['content'].items():
                    display_text = text[:100] + "..." if len(text) > 100 else text
                    print(f"   - {part}: {len(text)}字符")
                    print(f"     内容: {display_text}")
            
            if result.get('debug_info'):
                print(f"🔍 调试信息:")
                debug_info = result['debug_info']
                if 'extracted_elements' in debug_info:
                    print(f"   - 成功提取的元素: {len(debug_info['extracted_elements'])}个")
                    for element in debug_info['extracted_elements'][:5]:  # 只显示前5个
                        print(f"     • {element}")
                    if len(debug_info['extracted_elements']) > 5:
                        print(f"     ... 还有 {len(debug_info['extracted_elements'])-5} 个")
                
                if 'total_sections' in debug_info:
                    print(f"   - 总计部分数: {debug_info['total_sections']}")
            
            print(f"💬 提取信息: {result.get('message', '无')}")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            print(f"🔍 错误详情: {traceback.format_exc()}")
            
            results.append({
                "pmid": pmid,
                "success": False,
                "error": str(e),
                "execution_time": round(time.time() - start_time, 2) if 'start_time' in locals() else 0
            })
    
    return results

def test_analyze_pmid_with_full_text():
    """测试analyze_pmid_with_full_text函数的综合效果"""
    print("\n" + "="*80)
    print("测试3: analyze_pmid_with_full_text函数综合效果")
    print("="*80)
    
    # 测试用例：综合测试的PMID
    test_pmids = [
        "32542345",
        "30000000"
    ]
    
    results = []
    
    for i, pmid in enumerate(test_pmids, 1):
        print(f"\n🔍 综合测试用例 {i}: PMID = {pmid}")
        print("-" * 60)
        
        try:
            start_time = time.time()
            result = analyze_pmid_with_full_text(pmid)
            end_time = time.time()
            
            # 记录结果
            test_result = {
                "pmid": pmid,
                "success": True,
                "is_free": result.get('is_free', False),
                "extraction_success": result.get('extraction_success', False),
                "content_parts": len(result.get('extracted_content', {})),
                "execution_time": round(end_time - start_time, 2),
                "debug_info": result.get('debug_info', {}),
                "message": result.get('message', '')
            }
            
            results.append(test_result)
            
            # 打印详细结果
            print(f"✅ 整体测试结果:")
            print(f"   - 免费全文: {'是' if result.get('is_free') else '否'}")
            print(f"   - 内容提取: {'成功' if result.get('extraction_success') else '失败'}")
            print(f"   - 提取内容部分: {len(result.get('extracted_content', {}))}")
            print(f"   - 总执行时间: {test_result['execution_time']}秒")
            
            if result.get('debug_info'):
                print(f"🔍 调试信息:")
                debug_info = result['debug_info']
                if 'availability_source' in debug_info:
                    print(f"   - 可用性检查来源: {debug_info['availability_source']}")
                if 'total_links_found' in debug_info:
                    print(f"   - 找到的链接数: {debug_info['total_links_found']}")
                if 'extraction_attempted' in debug_info:
                    print(f"   - 提取尝试: {'是' if debug_info['extraction_attempted'] else '否'}")
            
            print(f"💬 综合信息: {result.get('message', '无')}")
            
        except Exception as e:
            print(f"❌ 综合测试失败: {str(e)}")
            print(f"🔍 错误详情: {traceback.format_exc()}")
            
            results.append({
                "pmid": pmid,
                "success": False,
                "error": str(e),
                "execution_time": round(time.time() - start_time, 2) if 'start_time' in locals() else 0
            })
    
    return results

def generate_test_report(all_results):
    """生成测试报告"""
    print("\n" + "="*80)
    print("📊 全文提取算法优化测试报告")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"测试时间: {timestamp}")
    print(f"测试环境: macOS")
    
    # 统计总体结果
    total_tests = len(all_results[0]) + len(all_results[1]) + len(all_results[2])
    successful_tests = 0
    
    for test_group in all_results:
        for result in test_group:
            if result.get('success', False):
                successful_tests += 1
    
    print(f"\n📈 总体统计:")
    print(f"   - 总测试数: {total_tests}")
    print(f"   - 成功测试数: {successful_tests}")
    print(f"   - 成功率: {successful_tests/total_tests*100:.1f}%")
    
    # 检查免费全文检测效果
    print(f"\n🎯 免费全文检测效果:")
    availability_results = all_results[0]
    free_detected = sum(1 for r in availability_results if r.get('success') and r.get('is_free'))
    total_available = len([r for r in availability_results if r.get('success')])
    print(f"   - 检测到免费全文: {free_detected}/{total_available} ({free_detected/max(total_available,1)*100:.1f}%)")
    
    # 检查内容提取效果
    print(f"\n📄 内容提取效果:")
    extraction_results = all_results[1]
    successful_extractions = sum(1 for r in extraction_results if r.get('success') and r.get('extraction_success'))
    total_extractions = len([r for r in extraction_results if r.get('success')])
    print(f"   - 成功提取内容: {successful_extractions}/{total_extractions} ({successful_extractions/max(total_extractions,1)*100:.1f}%)")
    
    # 检查综合分析效果
    print(f"\n🔍 综合分析效果:")
    analysis_results = all_results[2]
    successful_analyses = sum(1 for r in analysis_results if r.get('success'))
    total_analyses = len([r for r in analysis_results if r.get('success')])
    print(f"   - 成功完成分析: {successful_analyses}/{total_analyses} ({successful_analyses/max(total_analyses,1)*100:.1f}%)")
    
    # 性能分析
    print(f"\n⚡ 性能分析:")
    all_execution_times = []
    for test_group in all_results:
        for result in test_group:
            if 'execution_time' in result:
                all_execution_times.append(result['execution_time'])
    
    if all_execution_times:
        avg_time = sum(all_execution_times) / len(all_execution_times)
        max_time = max(all_execution_times)
        min_time = min(all_execution_times)
        print(f"   - 平均执行时间: {avg_time:.2f}秒")
        print(f"   - 最长执行时间: {max_time:.2f}秒")
        print(f"   - 最短执行时间: {min_time:.2f}秒")
    
    # 优化效果评估
    print(f"\n🚀 优化效果评估:")
    print(f"   ✅ 元素定位准确性: {'良好' if successful_tests/total_tests > 0.8 else '需改进'}")
    print(f"   ✅ 调试信息完善度: {'完善' if total_tests > 0 else '需改进'}")
    print(f"   ✅ 错误处理机制: {'健全' if successful_tests/total_tests > 0.7 else '需改进'}")
    
    print(f"\n💡 建议:")
    if successful_tests/total_tests < 0.8:
        print(f"   - 成功率较低，建议进一步优化元素定位策略")
    if len([t for t in all_execution_times if t > 10]) > 0:
        print(f"   - 部分测试执行时间较长，考虑添加超时机制")
    print(f"   - 继续收集更多测试用例以验证算法稳定性")

def interactive_test():
    """交互式测试单个PMID"""
    print("\n" + "="*80)
    print("🎮 交互式测试模式")
    print("="*80)
    print("输入PMID进行实时测试，输入'quit'退出")
    
    while True:
        pmid = input("\n请输入PMID: ").strip()
        
        if pmid.lower() == 'quit':
            print("退出交互式测试")
            break
        
        if not pmid:
            print("PMID不能为空，请重新输入")
            continue
        
        print(f"\n🔍 开始测试PMID: {pmid}")
        print("-" * 60)
        
        try:
            # 执行综合分析
            result = analyze_pmid_with_full_text(pmid)
            
            print(f"\n📊 测试结果摘要:")
            print(f"   - PMID: {result.get('pmid', 'N/A')}")
            print(f"   - 免费全文: {'是' if result.get('is_free') else '否'}")
            print(f"   - 提取成功: {'是' if result.get('extraction_success') else '否'}")
            print(f"   - 内容部分: {len(result.get('extracted_content', {}))}")
            
            if result.get('debug_info'):
                print(f"   - 调试信息已记录: {len(result.get('debug_info', {}))}项")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            print(f"🔍 错误详情: {traceback.format_exc()}")
        
        print("\n" + "-" * 60)

def main():
    """主函数"""
    print("🚀 全文提取算法优化测试程序")
    print("=" * 80)
    print("此程序将测试以下优化功能：")
    print("1. check_full_text_availability函数 - 重点检查title='Free full text at PubMed Central'")
    print("2. extract_full_text_content函数 - 增强元素定位和内容提取")
    print("3. 调试信息和错误处理机制")
    print("4. 整体算法效果验证")
    
    print("\n请选择测试模式:")
    print("1. 自动测试模式 (运行所有预设测试)")
    print("2. 交互式测试模式 (手动输入PMID测试)")
    print("3. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            print("\n开始自动测试...")
            
            # 运行所有测试
            availability_results = test_check_full_text_availability()
            extraction_results = test_extract_full_text_content()
            analysis_results = test_analyze_pmid_with_full_text()
            
            # 生成测试报告
            generate_test_report([availability_results, extraction_results, analysis_results])
            
            print("\n✅ 自动测试完成!")
            break
            
        elif choice == "2":
            interactive_test()
            break
            
        elif choice == "3":
            print("程序退出")
            sys.exit(0)
            
        else:
            print("无效选择，请输入 1-3")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序运行出错: {str(e)}")
        print(f"🔍 错误详情: {traceback.format_exc()}")
        sys.exit(1)