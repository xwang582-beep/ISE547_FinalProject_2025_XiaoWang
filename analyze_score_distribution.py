#!/usr/bin/env python3
"""
分析评估结果的分数分布
帮助理解评估结果的分布特征，而不仅仅依赖平均值
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import statistics

def load_evaluation_results(output_dir="output"):
    """加载所有评估结果文件"""
    results = {}
    output_path = Path(output_dir)
    
    for json_file in output_path.glob("*_evaluation.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            results[json_file.stem] = data
    
    return results

def analyze_distribution(scores):
    """分析分数分布"""
    if not scores:
        return None
    
    scores_sorted = sorted(scores)
    
    # 基本统计
    mean = statistics.mean(scores)
    median = statistics.median(scores)
    stdev = statistics.stdev(scores) if len(scores) > 1 else 0
    
    # 分位数
    q25 = scores_sorted[len(scores_sorted) // 4]
    q75 = scores_sorted[3 * len(scores_sorted) // 4]
    
    # 分布区间
    high = sum(1 for s in scores if s >= 0.7)
    medium = sum(1 for s in scores if 0.5 <= s < 0.7)
    low = sum(1 for s in scores if s < 0.5)
    
    total = len(scores)
    
    return {
        'count': total,
        'mean': mean,
        'median': median,
        'stdev': stdev,
        'q25': q25,
        'q75': q75,
        'min': min(scores),
        'max': max(scores),
        'high_count': high,
        'high_pct': high / total * 100,
        'medium_count': medium,
        'medium_pct': medium / total * 100,
        'low_count': low,
        'low_pct': low / total * 100,
    }

def analyze_faq_distribution(results):
    """分析所有FAQ的分数分布"""
    all_stats = {}
    
    for filename, data in results.items():
        stats = {}
        
        # 提取所有一致性分数
        # 方法1：从results列表中提取
        consistency_scores = []
        if data.get('results'):
            for result in data.get('results', []):
                score = result.get('consistency_score')
                if score is not None:
                    consistency_scores.append(score)
        
        # 方法2：如果results为空，尝试从faqs中提取
        if not consistency_scores:
            for faq in data.get('faqs', []):
                score = faq.get('consistency_score') or faq.get('qafacteval_consistency') or faq.get('questeval_consistency')
                if score is not None:
                    consistency_scores.append(score)
        
        # 方法3：如果都没有，使用平均一致性分数作为参考
        if not consistency_scores and data.get('average_consistency') is not None:
            # 无法获取详细分布，只能显示平均值
            stats['summary'] = {
                'count': data.get('total_faqs', 0),
                'average_consistency': data.get('average_consistency', 0),
                'consistency_rate': data.get('consistency_rate', 0),
                'note': '详细分数分布不可用，仅显示汇总统计'
            }
        elif consistency_scores:
            # 分析分布
            method = data.get('method', 'unknown')
            stats[method] = analyze_distribution(consistency_scores)
        
        all_stats[filename] = stats
    
    return all_stats

def print_distribution_report(stats):
    """打印分布报告"""
    print("=" * 80)
    print("📊 评估分数分布分析报告")
    print("=" * 80)
    print()
    
    for filename, file_stats in stats.items():
        print(f"\n📄 文件: {filename}")
        print("-" * 80)
        
        if not file_stats:
            print("  ⚠️  无评估数据")
            continue
        
        for method, dist in file_stats.items():
            if dist is None:
                continue
            
            if method == 'summary':
                print(f"\n  汇总统计:")
                print(f"    总数: {dist['count']}")
                print(f"    平均一致性: {dist['average_consistency']:.3f}")
                print(f"    一致性比例 (>0.7): {dist['consistency_rate']:.1%}")
                print(f"    注意: {dist['note']}")
            else:
                print(f"\n  {method.upper()} 方法:")
                print(f"    总数: {dist['count']}")
                print(f"    平均值: {dist['mean']:.3f}")
                print(f"    中位数: {dist['median']:.3f}")
                print(f"    标准差: {dist['stdev']:.3f}")
                print(f"    范围: [{dist['min']:.3f}, {dist['max']:.3f}]")
                print(f"    四分位数: Q25={dist['q25']:.3f}, Q75={dist['q75']:.3f}")
                print()
                print(f"    分数分布:")
                print(f"      高分 (≥0.7): {dist['high_count']:4d} ({dist['high_pct']:5.1f}%)")
                print(f"      中分 (0.5-0.7): {dist['medium_count']:4d} ({dist['medium_pct']:5.1f}%)")
                print(f"      低分 (<0.5): {dist['low_count']:4d} ({dist['low_pct']:5.1f}%)")
            print()

def identify_patterns(stats):
    """识别分布模式"""
    print("=" * 80)
    print("🔍 分布模式分析")
    print("=" * 80)
    print()
    
    # 收集所有数据
    all_high_pcts = []
    all_medium_pcts = []
    all_low_pcts = []
    
    for filename, file_stats in stats.items():
        for method, dist in file_stats.items():
            if dist is None:
                continue
            # 跳过summary类型，它没有分布数据
            if method == 'summary' or 'high_pct' not in dist:
                continue
            all_high_pcts.append(dist['high_pct'])
            all_medium_pcts.append(dist['medium_pct'])
            all_low_pcts.append(dist['low_pct'])
    
    if all_high_pcts:
        print(f"📈 高分FAQ比例:")
        print(f"    平均: {statistics.mean(all_high_pcts):.1f}%")
        print(f"    范围: [{min(all_high_pcts):.1f}%, {max(all_high_pcts):.1f}%]")
        print()
    
    if all_medium_pcts:
        print(f"📊 中分FAQ比例:")
        print(f"    平均: {statistics.mean(all_medium_pcts):.1f}%")
        print(f"    范围: [{min(all_medium_pcts):.1f}%, {max(all_medium_pcts):.1f}%]")
        print()
    
    if all_low_pcts:
        print(f"📉 低分FAQ比例:")
        print(f"    平均: {statistics.mean(all_low_pcts):.1f}%")
        print(f"    范围: [{min(all_low_pcts):.1f}%, {max(all_low_pcts):.1f}%]")
        print()
    
    # 分析标准差
    print("💡 观察:")
    stdevs = [d['stdev'] for s in stats.values() for d in s.values() if d and 'stdev' in d]
    if stdevs:
        avg_stdev = statistics.mean(stdevs)
        if avg_stdev > 0.2:
            print("    - 分数分布较分散（标准差>0.2），表明FAQ质量差异较大")
        else:
            print("    - 分数分布较集中（标准差<0.2），表明FAQ质量相对一致")
    
    if all_low_pcts:
        avg_low_pct = statistics.mean(all_low_pcts)
        if avg_low_pct > 30:
            print(f"    - 低分FAQ比例较高（{avg_low_pct:.1f}%），建议分析低分原因")
        else:
            print(f"    - 低分FAQ比例较低（{avg_low_pct:.1f}%），整体质量较好")
    else:
        print("    - 无法分析详细分布（缺少详细分数数据）")
        print("    - 建议：检查评估结果文件是否包含详细的FAQ分数")

def main():
    """主函数"""
    print("正在加载评估结果...")
    results = load_evaluation_results()
    
    if not results:
        print("❌ 未找到评估结果文件（*_evaluation.json）")
        print("   请先运行评估脚本：python evaluate_with_course_methods.py")
        return
    
    print(f"✅ 找到 {len(results)} 个评估结果文件")
    print()
    
    # 分析分布
    stats = analyze_faq_distribution(results)
    
    # 打印报告
    print_distribution_report(stats)
    
    # 识别模式
    identify_patterns(stats)
    
    # 保存结果
    output_file = "output/score_distribution_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"✅ 分析结果已保存到: {output_file}")

if __name__ == "__main__":
    main()

