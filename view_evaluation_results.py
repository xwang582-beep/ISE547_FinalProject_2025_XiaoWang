"""
查看评估结果的便捷脚本
"""

import json
import glob
from pathlib import Path
from collections import defaultdict

def view_summary():
    """查看所有评估结果的总体统计"""
    print("="*70)
    print("📊 FAQ质量评估结果 - 总体统计")
    print("="*70)
    
    files = glob.glob('output/*_evaluation.json')
    files = [f for f in files if 'analysis_report' not in f]
    
    if not files:
        print("❌ 未找到评估结果文件！")
        return
    
    results_by_doc = defaultdict(dict)
    
    for file in sorted(files):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 解析文件名
        filename = Path(file).stem.replace('_evaluation', '')
        parts = filename.split('_faqs_')
        
        if len(parts) == 2:
            doc_name = parts[0]
            model = parts[1]
            
            results_by_doc[doc_name][model] = {
                'total_faqs': data['total_faqs'],
                'average_consistency': data['average_consistency'],
                'consistency_rate': data['consistency_rate'],
                'consistent_count': int(data['consistency_rate'] * data['total_faqs'])
            }
    
    # 打印表格
    print(f"\n{'文档':<20} {'模型':<10} {'FAQ数':<10} {'平均一致性':<15} {'一致性比例':<15}")
    print("-"*70)
    
    total_openai = 0
    total_claude = 0
    total_consistent_openai = 0
    total_consistent_claude = 0
    
    for doc_name in sorted(results_by_doc.keys()):
        doc_display = doc_name.replace('_', ' ').title()
        
        if 'openai' in results_by_doc[doc_name]:
            r = results_by_doc[doc_name]['openai']
            total_openai += r['total_faqs']
            total_consistent_openai += r['consistent_count']
            print(f"{doc_display:<20} {'OpenAI':<10} {r['total_faqs']:<10} "
                  f"{r['average_consistency']:<15.3f} {r['consistency_rate']:<15.1%}")
        
        if 'claude' in results_by_doc[doc_name]:
            r = results_by_doc[doc_name]['claude']
            total_claude += r['total_faqs']
            total_consistent_claude += r['consistent_count']
            print(f"{doc_display:<20} {'Claude':<10} {r['total_faqs']:<10} "
                  f"{r['average_consistency']:<15.3f} {r['consistency_rate']:<15.1%}")
        print()
    
    # 总体统计
    print("-"*70)
    if total_openai > 0:
        avg_openai = total_consistent_openai / total_openai
        print(f"{'总计 (OpenAI)':<20} {'':<10} {total_openai:<10} "
              f"{'':<15} {avg_openai:.1%}")
    if total_claude > 0:
        avg_claude = total_consistent_claude / total_claude
        print(f"{'总计 (Claude)':<20} {'':<10} {total_claude:<10} "
              f"{'':<15} {avg_claude:.1%}")


def view_detailed(file_path, show_count=5):
    """查看单个文件的详细结果"""
    print("="*70)
    print(f"📋 详细评估结果: {Path(file_path).name}")
    print("="*70)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n总体统计:")
    print(f"  总FAQ数: {data['total_faqs']}")
    print(f"  平均一致性: {data['average_consistency']:.3f}")
    print(f"  一致性比例 (>0.7): {data['consistency_rate']:.1%}")
    print(f"  一致FAQ数: {int(data['consistency_rate'] * data['total_faqs'])}/{data['total_faqs']}")
    
    # 显示高分FAQ
    high_scores = [r for r in data['results'] if r['consistency_score'] > 0.8]
    if high_scores:
        print(f"\n✅ 高分FAQ示例（一致性>0.8，显示前{show_count}个）:")
        for i, r in enumerate(high_scores[:show_count], 1):
            print(f"\n  {i}. 分数: {r['consistency_score']:.2f}")
            print(f"     问题: {r['question']}")
            print(f"     答案: {r['answer'][:150]}...")
    
    # 显示低分FAQ
    low_scores = [r for r in data['results'] if r['consistency_score'] < 0.5]
    if low_scores:
        print(f"\n❌ 低分FAQ示例（一致性<0.5，显示前{show_count}个）:")
        for i, r in enumerate(low_scores[:show_count], 1):
            print(f"\n  {i}. 分数: {r['consistency_score']:.2f}")
            print(f"     问题: {r['question']}")
            print(f"     答案: {r['answer'][:150]}...")
    
    # 分数分布
    scores = [r['consistency_score'] for r in data['results']]
    if scores:
        print(f"\n📊 分数分布:")
        print(f"  最高分: {max(scores):.3f}")
        print(f"  最低分: {min(scores):.3f}")
        print(f"  中位数: {sorted(scores)[len(scores)//2]:.3f}")
        
        # 分数区间统计
        ranges = {
            '优秀 (>0.8)': sum(1 for s in scores if s > 0.8),
            '良好 (0.7-0.8)': sum(1 for s in scores if 0.7 <= s <= 0.8),
            '中等 (0.5-0.7)': sum(1 for s in scores if 0.5 <= s < 0.7),
            '较差 (<0.5)': sum(1 for s in scores if s < 0.5)
        }
        
        print(f"\n  分数区间分布:")
        for range_name, count in ranges.items():
            pct = count / len(scores) * 100
            print(f"    {range_name}: {count} ({pct:.1f}%)")


def view_comparison():
    """对比OpenAI和Claude的结果"""
    print("="*70)
    print("📊 OpenAI vs Claude 对比分析")
    print("="*70)
    
    files = glob.glob('output/*_evaluation.json')
    files = [f for f in files if 'analysis_report' not in f]
    
    results_by_doc = defaultdict(dict)
    
    for file in sorted(files):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        filename = Path(file).stem.replace('_evaluation', '')
        parts = filename.split('_faqs_')
        
        if len(parts) == 2:
            doc_name = parts[0]
            model = parts[1]
            results_by_doc[doc_name][model] = data
    
    for doc_name in sorted(results_by_doc.keys()):
        if 'openai' in results_by_doc[doc_name] and 'claude' in results_by_doc[doc_name]:
            doc_display = doc_name.replace('_', ' ').title()
            openai_data = results_by_doc[doc_name]['openai']
            claude_data = results_by_doc[doc_name]['claude']
            
            print(f"\n{doc_display}:")
            print(f"  OpenAI: 平均一致性={openai_data['average_consistency']:.3f}, "
                  f"一致性比例={openai_data['consistency_rate']:.1%}")
            print(f"  Claude: 平均一致性={claude_data['average_consistency']:.3f}, "
                  f"一致性比例={claude_data['consistency_rate']:.1%}")
            
            diff = openai_data['average_consistency'] - claude_data['average_consistency']
            if abs(diff) > 0.05:
                winner = "OpenAI" if diff > 0 else "Claude"
                print(f"  → {winner}表现更好（差异: {abs(diff):.3f}）")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            view_summary()
        elif sys.argv[1] == "comparison":
            view_comparison()
        elif sys.argv[1].startswith("output/"):
            view_detailed(sys.argv[1])
        else:
            print("用法:")
            print("  python view_evaluation_results.py summary      # 查看总体统计")
            print("  python view_evaluation_results.py comparison   # 查看对比分析")
            print("  python view_evaluation_results.py output/xxx_evaluation.json  # 查看详细结果")
    else:
        # 默认显示总体统计
        view_summary()
        print("\n" + "="*70)
        print("💡 更多选项:")
        print("  python view_evaluation_results.py summary      # 查看总体统计")
        print("  python view_evaluation_results.py comparison   # 查看对比分析")
        print("  python view_evaluation_results.py output/genai_faqs_openai_evaluation.json  # 查看详细结果")


if __name__ == "__main__":
    main()

