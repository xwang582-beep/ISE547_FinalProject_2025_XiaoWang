#!/usr/bin/env python3
"""
选择手动验证的FAQ样本
从每个文档中选择不同质量水平的FAQ，生成便于验证的格式
"""

import json
import random
from pathlib import Path
from collections import defaultdict

def load_faqs_from_evaluation(eval_file):
    """从评估结果文件中加载FAQ"""
    with open(eval_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 从results中提取FAQ
    faqs = []
    for result in data.get('results', []):
        faq = {
            'question': result.get('question', ''),
            'answer': result.get('answer', ''),
            'consistency_score': result.get('consistency_score', 0),
            'is_consistent': result.get('is_consistent', False),
            'faq_index': result.get('faq_index', 0)
        }
        faqs.append(faq)
    
    return faqs, data.get('file', ''), data.get('method', '')

def load_faqs_from_original(original_file):
    """从原始FAQ文件中加载完整FAQ信息"""
    try:
        with open(original_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('faqs', [])
    except:
        return []

def categorize_faqs(faqs):
    """将FAQ按分数分类"""
    high = []  # >= 0.7
    medium = []  # 0.5 - 0.7
    low = []  # < 0.5
    
    for faq in faqs:
        score = faq.get('consistency_score', 0)
        if score >= 0.7:
            high.append(faq)
        elif score >= 0.5:
            medium.append(faq)
        else:
            low.append(faq)
    
    return high, medium, low

def select_samples(high, medium, low, total_samples=20):
    """从不同类别中选择样本"""
    # 分配样本数量：40%高分，30%中分，30%低分
    high_count = max(1, int(total_samples * 0.4))
    medium_count = max(1, int(total_samples * 0.3))
    low_count = max(1, total_samples - high_count - medium_count)
    
    # 如果某个类别数量不足，从其他类别补充
    selected = []
    
    # 选择高分
    if high:
        high_samples = random.sample(high, min(high_count, len(high)))
        selected.extend(high_samples)
        remaining = total_samples - len(selected)
    else:
        remaining = total_samples
    
    # 选择中分
    if medium and remaining > 0:
        medium_samples = random.sample(medium, min(medium_count, len(medium), remaining))
        selected.extend(medium_samples)
        remaining = total_samples - len(selected)
    
    # 选择低分
    if low and remaining > 0:
        low_samples = random.sample(low, min(low_count, len(low), remaining))
        selected.extend(low_samples)
    
    # 如果还不够，从所有类别中随机补充
    all_faqs = high + medium + low
    while len(selected) < total_samples and len(selected) < len(all_faqs):
        remaining_faqs = [f for f in all_faqs if f not in selected]
        if not remaining_faqs:
            break
        selected.append(random.choice(remaining_faqs))
    
    return selected

def generate_verification_document(samples_by_file):
    """生成手动验证文档"""
    markdown = """# 📋 FAQ手动验证样本

## 📊 验证说明

本文档包含从所有文档中随机选择的FAQ样本，用于手动验证自动化评估的准确性。

### 验证标准

1. **准确性（Accuracy）**
   - ✅ **准确**：答案完全基于源文档，信息正确
   - ⚠️ **部分准确**：答案基本正确，但缺少细节或略有偏差
   - ❌ **不准确**：答案包含错误信息或与源文档不符

2. **相关性（Relevance）**
   - ✅ **高度相关**：问题直接对应文档中的明确信息
   - ⚠️ **部分相关**：问题相关但答案不够具体
   - ❌ **不相关**：问题与文档内容关系不大

3. **自然度（Naturalness）**
   - ✅ **自然**：问题像人类会问的问题，答案流畅
   - ⚠️ **一般**：问题或答案略显生硬
   - ❌ **不自然**：问题或答案明显是机器生成的

4. **完整性（Completeness）**
   - ✅ **完整**：答案充分回答了问题
   - ⚠️ **部分完整**：答案回答了问题但不够详细
   - ❌ **不完整**：答案没有充分回答问题

### 验证方法

1. 阅读每个FAQ的问题和答案
2. 在源文档中查找相关信息
3. 评估准确性、相关性、自然度、完整性
4. 记录与自动化评估的一致性分数是否匹配
5. 特别关注低分FAQ，检查是否存在表达偏差（答案正确但表达不同）

---

"""
    
    total_faqs = 0
    
    for filename, samples in samples_by_file.items():
        doc_name = filename.replace('_evaluation', '').replace('_faqs', '').replace('_', ' ').title()
        method = samples[0].get('method', 'Unknown')
        
        markdown += f"## 📄 {doc_name}\n\n"
        markdown += f"**评估方法**: {method.upper()}\n\n"
        markdown += f"**样本数量**: {len(samples)} 个FAQ\n\n"
        markdown += "---\n\n"
        
        for i, sample in enumerate(samples, 1):
            question = sample.get('question', 'N/A')
            answer = sample.get('answer', 'N/A')
            score = sample.get('consistency_score', 0)
            is_consistent = sample.get('is_consistent', False)
            quality_level = "高分" if score >= 0.7 else ("中分" if score >= 0.5 else "低分")
            
            markdown += f"### FAQ #{i} - {quality_level} (一致性分数: {score:.3f})\n\n"
            markdown += f"**问题**:\n```\n{question}\n```\n\n"
            markdown += f"**答案**:\n```\n{answer}\n```\n\n"
            markdown += f"**自动化评估**:\n"
            markdown += f"- 一致性分数: **{score:.3f}**\n"
            markdown += f"- 是否一致 (>0.7): {'✅ 是' if is_consistent else '❌ 否'}\n"
            markdown += f"- 质量等级: **{quality_level}**\n\n"
            markdown += "**人工评估**:\n"
            markdown += "- 准确性: [ ] ✅ 准确  [ ] ⚠️ 部分准确  [ ] ❌ 不准确\n"
            markdown += "- 相关性: [ ] ✅ 高度相关  [ ] ⚠️ 部分相关  [ ] ❌ 不相关\n"
            markdown += "- 自然度: [ ] ✅ 自然  [ ] ⚠️ 一般  [ ] ❌ 不自然\n"
            markdown += "- 完整性: [ ] ✅ 完整  [ ] ⚠️ 部分完整  [ ] ❌ 不完整\n\n"
            markdown += "**在源文档中的位置**:\n"
            markdown += "- 章节/页码: _______________\n\n"
            markdown += "**观察**:\n"
            markdown += "- [ ] 答案包含源文档没有的信息\n"
            markdown += "- [ ] 答案过于概括，缺少细节\n"
            markdown += "- [ ] 答案表达方式不同但意思相同（可能是评估偏差）\n"
            markdown += "- [ ] 其他问题: _______________\n\n"
            markdown += "**备注**:\n```\n\n```\n\n"
            markdown += "---\n\n"
        
        total_faqs += len(samples)
    
    markdown += f"\n## 📊 统计总结\n\n"
    markdown += f"**总验证样本数**: {total_faqs} 个FAQ\n\n"
    markdown += "### 验证完成后，请填写以下统计：\n\n"
    markdown += "**准确性分布**:\n"
    markdown += "- ✅ 准确: ____ (____%)\n"
    markdown += "- ⚠️ 部分准确: ____ (____%)\n"
    markdown += "- ❌ 不准确: ____ (____%)\n\n"
    markdown += "**与自动化评估的一致性**:\n"
    markdown += "- 高一致性分数（>0.7）的FAQ中，人工评估为准确的比例: ____ / ____ (____%)\n"
    markdown += "- 低一致性分数（<0.5）的FAQ中，人工评估为准确的比例: ____ / ____ (____%)\n"
    markdown += "- 总体一致性: ____%\n\n"
    markdown += "**主要发现**:\n```\n\n```\n\n"
    
    return markdown

def main():
    """主函数"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='选择手动验证的FAQ样本')
    parser.add_argument('samples', type=int, nargs='?', default=20,
                       help='每个文档选择的样本数（默认：20）')
    parser.add_argument('--low-score-only', action='store_true',
                       help='只选择低分FAQ（<0.5）')
    parser.add_argument('--high-score-only', action='store_true',
                       help='只选择高分FAQ（≥0.7）')
    
    args = parser.parse_args()
    samples_per_file = args.samples
    low_score_only = args.low_score_only
    high_score_only = args.high_score_only
    
    print("=" * 80)
    print("📋 选择手动验证样本")
    print("=" * 80)
    print(f"\n每个文档选择样本数: {samples_per_file}")
    if low_score_only:
        print("模式: 只选择低分FAQ（<0.5）")
    elif high_score_only:
        print("模式: 只选择高分FAQ（≥0.7）")
    else:
        print("模式: 覆盖不同质量水平（高分40%，中分30%，低分30%）")
    print()
    
    # 查找所有评估结果文件
    output_dir = Path("output")
    eval_files = list(output_dir.glob("*_evaluation.json"))
    eval_files = [f for f in eval_files if 'analysis_report' not in f.name]
    
    if not eval_files:
        print("❌ 未找到评估结果文件！")
        print("   请先运行评估脚本：python evaluate_with_course_methods.py")
        return
    
    print(f"✅ 找到 {len(eval_files)} 个评估结果文件")
    print()
    
    # 处理每个文件
    all_samples = {}
    
    for eval_file in sorted(eval_files):
        print(f"处理: {eval_file.name}")
        
        # 加载FAQ
        faqs, original_file, method = load_faqs_from_evaluation(eval_file)
        
        if not faqs:
            print(f"  ⚠️  未找到FAQ数据，跳过")
            continue
        
        print(f"  总FAQ数: {len(faqs)}")
        
        # 分类
        high, medium, low = categorize_faqs(faqs)
        print(f"  高分 (≥0.7): {len(high)}, 中分 (0.5-0.7): {len(medium)}, 低分 (<0.5): {len(low)}")
        
        # 选择样本
        if low_score_only:
            # 只选择低分FAQ
            if low:
                selected = random.sample(low, min(samples_per_file, len(low)))
            else:
                print(f"  ⚠️  没有低分FAQ，跳过")
                continue
        elif high_score_only:
            # 只选择高分FAQ
            if high:
                selected = random.sample(high, min(samples_per_file, len(high)))
            else:
                print(f"  ⚠️  没有高分FAQ，跳过")
                continue
        else:
            # 正常选择（覆盖不同质量水平）
            selected = select_samples(high, medium, low, samples_per_file)
        
        # 添加方法信息
        for s in selected:
            s['method'] = method
        
        all_samples[eval_file.stem] = selected
        print(f"  ✅ 选择了 {len(selected)} 个样本")
        print()
    
    # 生成验证文档
    print("生成验证文档...")
    verification_doc = generate_verification_document(all_samples)
    
    # 保存
    output_file = "manual_verification_samples.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(verification_doc)
    
    print(f"✅ 验证文档已保存到: {output_file}")
    print()
    print("=" * 80)
    print("📝 下一步:")
    print("=" * 80)
    print(f"1. 打开 {output_file} 文件")
    print("2. 逐个验证每个FAQ")
    print("3. 填写评估结果")
    print("4. 完成后统计结果，与自动化评估对比")
    print()
    print("💡 提示:")
    print("- 特别关注低分FAQ，检查是否存在表达偏差")
    print("- 记录在源文档中的位置，便于验证准确性")
    print("- 如果发现自动化评估与人工评估差异较大，记录下来")

if __name__ == "__main__":
    main()

