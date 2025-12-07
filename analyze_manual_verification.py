#!/usr/bin/env python3
"""
分析手动验证结果
从填写好的验证文档中提取统计信息
"""

import re
from collections import defaultdict

def parse_verification_document(filename="manual_verification_samples.md"):
    """解析验证文档"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = []
    current_faq = {}
    
    # 匹配FAQ块
    faq_pattern = r'### FAQ #(\d+) - (高分|中分|低分) \(一致性分数: ([\d.]+)\)'
    
    for match in re.finditer(faq_pattern, content):
        faq_num = match.group(1)
        quality_level = match.group(2)
        auto_score = float(match.group(3))
        
        # 提取问题
        question_match = re.search(r'\*\*问题\*\*:\n```\n(.*?)\n```', content[match.end():match.end()+2000], re.DOTALL)
        question = question_match.group(1).strip() if question_match else ""
        
        # 提取答案
        answer_match = re.search(r'\*\*答案\*\*:\n```\n(.*?)\n```', content[match.end():match.end()+2000], re.DOTALL)
        answer = answer_match.group(1).strip() if answer_match else ""
        
        # 提取人工评估（如果已填写）
        accuracy_match = re.search(r'准确性:.*?\[([xX ])\].*?✅.*?\[([xX ])\].*?⚠️.*?\[([xX ])\].*?❌', content[match.end():match.end()+500])
        relevance_match = re.search(r'相关性:.*?\[([xX ])\].*?✅.*?\[([xX ])\].*?⚠️.*?\[([xX ])\].*?❌', content[match.end():match.end()+500])
        naturalness_match = re.search(r'自然度:.*?\[([xX ])\].*?✅.*?\[([xX ])\].*?⚠️.*?\[([xX ])\].*?❌', content[match.end():match.end()+500])
        completeness_match = re.search(r'完整性:.*?\[([xX ])\].*?✅.*?\[([xX ])\].*?⚠️.*?\[([xX ])\].*?❌', content[match.end():match.end()+500])
        
        # 判断评估结果
        def get_rating(match_obj):
            if not match_obj:
                return None
            if match_obj.group(1).lower() == 'x':
                return 'high'
            elif match_obj.group(2).lower() == 'x':
                return 'medium'
            elif match_obj.group(3).lower() == 'x':
                return 'low'
            return None
        
        accuracy = get_rating(accuracy_match)
        relevance = get_rating(relevance_match)
        naturalness = get_rating(naturalness_match)
        completeness = get_rating(completeness_match)
        
        # 检查是否有表达偏差标记
        bias_match = re.search(r'答案表达方式不同但意思相同.*?\[([xX ])\]', content[match.end():match.end()+1000], re.DOTALL)
        has_expression_bias = bias_match and bias_match.group(1).lower() == 'x'
        
        results.append({
            'faq_num': faq_num,
            'quality_level': quality_level,
            'auto_score': auto_score,
            'question': question[:50] + '...' if len(question) > 50 else question,
            'answer': answer[:50] + '...' if len(answer) > 50 else answer,
            'accuracy': accuracy,
            'relevance': relevance,
            'naturalness': naturalness,
            'completeness': completeness,
            'has_expression_bias': has_expression_bias
        })
    
    return results

def analyze_results(results):
    """分析验证结果"""
    total = len(results)
    if total == 0:
        print("❌ 未找到验证结果！")
        return
    
    # 统计准确性
    accuracy_stats = defaultdict(int)
    for r in results:
        if r['accuracy']:
            accuracy_stats[r['accuracy']] += 1
    
    # 统计相关性
    relevance_stats = defaultdict(int)
    for r in results:
        if r['relevance']:
            relevance_stats[r['relevance']] += 1
    
    # 统计自然度
    naturalness_stats = defaultdict(int)
    for r in results:
        if r['naturalness']:
            naturalness_stats[r['naturalness']] += 1
    
    # 统计完整性
    completeness_stats = defaultdict(int)
    for r in results:
        if r['completeness']:
            completeness_stats[r['completeness']] += 1
    
    # 按自动化评估分数分类
    high_auto = [r for r in results if r['auto_score'] >= 0.7]
    low_auto = [r for r in results if r['auto_score'] < 0.5]
    
    # 高自动化分数中，人工评估为准确的比例
    high_auto_accurate = sum(1 for r in high_auto if r['accuracy'] == 'high')
    high_auto_accurate_pct = (high_auto_accurate / len(high_auto) * 100) if high_auto else 0
    
    # 低自动化分数中，人工评估为准确的比例
    low_auto_accurate = sum(1 for r in low_auto if r['accuracy'] == 'high')
    low_auto_accurate_pct = (low_auto_accurate / len(low_auto) * 100) if low_auto else 0
    
    # 表达偏差统计
    expression_bias_count = sum(1 for r in results if r['has_expression_bias'])
    
    # 打印报告
    print("=" * 80)
    print("📊 手动验证结果分析")
    print("=" * 80)
    print()
    print(f"总验证样本数: {total}")
    print()
    
    # 准确性分布
    print("📈 准确性分布:")
    if accuracy_stats:
        high_count = accuracy_stats.get('high', 0)
        medium_count = accuracy_stats.get('medium', 0)
        low_count = accuracy_stats.get('low', 0)
        total_rated = high_count + medium_count + low_count
        
        if total_rated > 0:
            print(f"  ✅ 准确: {high_count:3d} ({high_count/total_rated*100:5.1f}%)")
            print(f"  ⚠️  部分准确: {medium_count:3d} ({medium_count/total_rated*100:5.1f}%)")
            print(f"  ❌ 不准确: {low_count:3d} ({low_count/total_rated*100:5.1f}%)")
        else:
            print("  ⚠️  尚未填写准确性评估")
    else:
        print("  ⚠️  尚未填写准确性评估")
    print()
    
    # 相关性分布
    print("📊 相关性分布:")
    if relevance_stats:
        high_count = relevance_stats.get('high', 0)
        medium_count = relevance_stats.get('medium', 0)
        low_count = relevance_stats.get('low', 0)
        total_rated = high_count + medium_count + low_count
        
        if total_rated > 0:
            print(f"  ✅ 高度相关: {high_count:3d} ({high_count/total_rated*100:5.1f}%)")
            print(f"  ⚠️  部分相关: {medium_count:3d} ({medium_count/total_rated*100:5.1f}%)")
            print(f"  ❌ 不相关: {low_count:3d} ({low_count/total_rated*100:5.1f}%)")
    else:
        print("  ⚠️  尚未填写相关性评估")
    print()
    
    # 与自动化评估的对比
    print("🔍 与自动化评估的对比:")
    print(f"  高一致性分数（≥0.7）的FAQ: {len(high_auto)} 个")
    if high_auto:
        print(f"    其中人工评估为准确的比例: {high_auto_accurate}/{len(high_auto)} ({high_auto_accurate_pct:.1f}%)")
    
    print(f"  低一致性分数（<0.5）的FAQ: {len(low_auto)} 个")
    if low_auto:
        print(f"    其中人工评估为准确的比例: {low_auto_accurate}/{len(low_auto)} ({low_auto_accurate_pct:.1f}%)")
    print()
    
    # 表达偏差
    print("⚠️  表达偏差统计:")
    print(f"  发现表达偏差的FAQ: {expression_bias_count} 个 ({expression_bias_count/total*100:.1f}%)")
    print(f"  （答案正确但表达不同，导致自动化评估分数偏低）")
    print()
    
    # 总体一致性
    if accuracy_stats:
        total_rated = sum(accuracy_stats.values())
        if total_rated > 0:
            # 计算自动化评估与人工评估的一致性
            # 如果自动化评估为高分且人工评估为准确，或自动化评估为低分且人工评估为不准确，则认为一致
            consistent_count = 0
            for r in results:
                if r['accuracy']:
                    if (r['auto_score'] >= 0.7 and r['accuracy'] == 'high') or \
                       (r['auto_score'] < 0.5 and r['accuracy'] == 'low'):
                        consistent_count += 1
            
            consistency_pct = (consistent_count / total_rated * 100) if total_rated > 0 else 0
            print("📊 总体一致性:")
            print(f"  自动化评估与人工评估一致: {consistent_count}/{total_rated} ({consistency_pct:.1f}%)")
            print()
    
    # 建议
    print("💡 主要发现:")
    if expression_bias_count > 0:
        print(f"  - 发现 {expression_bias_count} 个FAQ存在表达偏差，证实了QAFactEval的局限性")
    if low_auto_accurate_pct > 20:
        print(f"  - 低分FAQ中有 {low_auto_accurate_pct:.1f}% 实际是准确的，表明存在评估偏差")
    if high_auto_accurate_pct < 80:
        print(f"  - 高分FAQ中只有 {high_auto_accurate_pct:.1f}% 被确认为准确，可能需要调整评估阈值")
    print()

def main():
    """主函数"""
    import sys
    
    # 默认使用填写好的文档
    filename = "manual_verification_samples_filled.md"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    print("正在解析验证文档...")
    try:
        results = parse_verification_document(filename)
        analyze_results(results)
    except FileNotFoundError:
        print(f"❌ 未找到验证文档: {filename}")
        print("   请先运行: python generate_verification_results.py")
    except Exception as e:
        print(f"❌ 解析错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

