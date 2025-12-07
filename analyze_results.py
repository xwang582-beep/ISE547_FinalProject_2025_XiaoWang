"""
Analyze FAQ generation results
统计和分析所有生成的FAQ结果
"""

import json
import glob
import os
from pathlib import Path
from collections import defaultdict

def analyze_results():
    """分析所有生成的FAQ结果"""
    
    print("="*70)
    print("📊 FAQ生成结果统计分析")
    print("="*70)
    
    # 收集所有JSON文件
    json_files = glob.glob('output/*.json')
    
    if not json_files:
        print("❌ 未找到任何JSON结果文件！")
        return
    
    # 按文档和模型分类
    results = defaultdict(dict)
    
    for json_file in sorted(json_files):
        filename = Path(json_file).stem
        parts = filename.split('_faqs_')
        
        if len(parts) == 2:
            doc_name = parts[0]
            model = parts[1]
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                results[doc_name][model] = {
                    'total_faqs': data.get('total_faqs', 0),
                    'chunks': data.get('metadata', {}).get('chunks', 0),
                    'model': data.get('metadata', {}).get('model', 'unknown'),
                    'provider': data.get('metadata', {}).get('provider', 'unknown'),
                    'generated_at': data.get('generated_at', 'unknown')
                }
    
    # 打印统计表格
    print("\n📋 各文档FAQ生成统计：")
    print("-"*70)
    print(f"{'文档':<25} {'模型':<15} {'FAQ数量':<12} {'分块数':<10}")
    print("-"*70)
    
    total_openai = 0
    total_claude = 0
    
    for doc_name in sorted(results.keys()):
        doc_display = doc_name.replace('_', ' ').title()
        
        if 'openai' in results[doc_name]:
            openai_data = results[doc_name]['openai']
            total_openai += openai_data['total_faqs']
            print(f"{doc_display:<25} {'OpenAI':<15} {openai_data['total_faqs']:<12} {openai_data['chunks']:<10}")
        
        if 'claude' in results[doc_name]:
            claude_data = results[doc_name]['claude']
            total_claude += claude_data['total_faqs']
            print(f"{doc_display:<25} {'Claude':<15} {claude_data['total_faqs']:<12} {claude_data['chunks']:<10}")
    
    print("-"*70)
    print(f"{'总计':<25} {'OpenAI':<15} {total_openai:<12}")
    print(f"{'总计':<25} {'Claude':<15} {total_claude:<12}")
    
    # 对比分析
    print("\n📊 OpenAI vs Claude 对比：")
    print("-"*70)
    
    for doc_name in sorted(results.keys()):
        if 'openai' in results[doc_name] and 'claude' in results[doc_name]:
            doc_display = doc_name.replace('_', ' ').title()
            openai_count = results[doc_name]['openai']['total_faqs']
            claude_count = results[doc_name]['claude']['total_faqs']
            diff = claude_count - openai_count
            diff_pct = (diff / openai_count * 100) if openai_count > 0 else 0
            
            print(f"{doc_display}:")
            print(f"  OpenAI: {openai_count} FAQs")
            print(f"  Claude: {claude_count} FAQs")
            print(f"  差异: {diff:+d} ({diff_pct:+.1f}%)")
            print()
    
    # 平均FAQ数量
    print("\n📈 平均统计：")
    print("-"*70)
    
    doc_count = len(results)
    if doc_count > 0:
        avg_openai = total_openai / doc_count if 'openai' in str(results) else 0
        avg_claude = total_claude / doc_count if 'claude' in str(results) else 0
        
        print(f"平均每个文档（OpenAI）: {avg_openai:.1f} FAQs")
        print(f"平均每个文档（Claude）: {avg_claude:.1f} FAQs")
    
    # 生成报告数据
    print("\n💾 生成报告数据...")
    
    report_data = {
        'summary': {
            'total_documents': doc_count,
            'total_openai_faqs': total_openai,
            'total_claude_faqs': total_claude,
            'avg_openai_per_doc': round(avg_openai, 1) if doc_count > 0 else 0,
            'avg_claude_per_doc': round(avg_claude, 1) if doc_count > 0 else 0
        },
        'by_document': {}
    }
    
    for doc_name in sorted(results.keys()):
        report_data['by_document'][doc_name] = results[doc_name]
    
    # 保存报告数据
    with open('output/analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print("✅ 报告数据已保存到: output/analysis_report.json")
    
    print("\n" + "="*70)
    print("✅ 分析完成！")
    print("="*70)
    
    # 建议
    print("\n💡 下一步建议：")
    print("1. 查看上面的统计数据")
    print("2. 手动检查每个文档的10-20个FAQ样本，评估质量")
    print("3. 创建对比分析报告（使用 PROJECT_REPORT_TEMPLATE.md）")
    print("4. 根据实际结果调整Expected Outcomes")


if __name__ == "__main__":
    analyze_results()

