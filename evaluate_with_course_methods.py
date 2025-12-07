"""
使用课程方法评估FAQ质量
基于QAFactEval和QuestEval方法
"""

import json
import glob
from pathlib import Path
from typing import List, Dict
import os

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class FAQEvaluator:
    """使用课程方法评估FAQ质量"""
    
    def __init__(self, api_key: str = None, provider: str = "openai"):
        """
        初始化评估器
        
        Args:
            api_key: API密钥
            provider: LLM提供商（openai或anthropic）
        """
        self.provider = provider.lower()
        
        if self.provider == "openai" and HAS_OPENAI:
            self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
            self.model = "gpt-3.5-turbo"
        elif self.provider == "anthropic" and HAS_ANTHROPIC:
            self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
            self.model = "claude-3-haiku-20240307"
        else:
            self.client = None
            print("⚠️  LLM客户端未初始化，将使用简化评估方法")
    
    def qafacteval_method(self, faq: Dict, source_chunk: str) -> Dict:
        """
        QAFactEval方法：从FAQ答案生成问题，在源文档中查找答案，评估一致性
        
        Args:
            faq: FAQ字典，包含'question'和'answer'
            source_chunk: 源文档的相关文本块
            
        Returns:
            评估结果字典
        """
        if not self.client:
            return self._simple_consistency_check(faq, source_chunk)
        
        # 步骤1: 从FAQ答案生成问题（使用LLM）
        questions = self._generate_questions_from_answer(faq['answer'])
        
        # 步骤2: 在源文档中查找这些问题的答案
        source_answers = []
        for question in questions:
            answer = self._find_answer_in_source(question, source_chunk)
            source_answers.append(answer)
        
        # 步骤3: 评估一致性
        consistency_score = self._calculate_consistency(
            faq['answer'],
            source_answers,
            questions
        )
        
        return {
            'method': 'QAFactEval',
            'consistency_score': consistency_score,
            'generated_questions': questions,
            'source_answers': source_answers,
            'is_consistent': consistency_score >= 0.7  # 阈值0.7
        }
    
    def questeval_method(self, faq: Dict, source_chunk: str) -> Dict:
        """
        QuestEval方法：从FAQ答案生成问题，在源文档和FAQ答案中找答案，比较一致性
        
        Args:
            faq: FAQ字典
            source_chunk: 源文档文本块
            
        Returns:
            评估结果字典
        """
        if not self.client:
            return self._simple_consistency_check(faq, source_chunk)
        
        # 步骤1: 从FAQ答案生成问题
        questions = self._generate_questions_from_answer(faq['answer'])
        
        # 步骤2: 在源文档中查找答案
        source_answers = [self._find_answer_in_source(q, source_chunk) 
                         for q in questions]
        
        # 步骤3: 在FAQ答案中查找答案（自验证）
        faq_answers = [self._extract_answer_from_faq(q, faq['answer']) 
                      for q in questions]
        
        # 步骤4: 计算一致性
        consistency = self._compare_answers(source_answers, faq_answers)
        
        return {
            'method': 'QuestEval',
            'consistency_score': consistency,
            'generated_questions': questions,
            'source_answers': source_answers,
            'faq_answers': faq_answers,
            'is_consistent': consistency >= 0.7
        }
    
    def _generate_questions_from_answer(self, answer: str) -> List[str]:
        """从答案生成问题"""
        if not self.client:
            # 简化版本：返回空列表
            return []
        
        prompt = f"""
        Generate 2-3 questions that could be answered by the following text.
        Return only the questions, one per line.
        
        Text:
        {answer}
        """
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100
                )
                text = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
            
            # 解析问题
            questions = [q.strip() for q in text.split('\n') if q.strip() and '?' in q]
            return questions[:3]  # 最多3个问题
            
        except Exception as e:
            print(f"生成问题失败: {str(e)}")
            return []
    
    def _find_answer_in_source(self, question: str, source: str) -> str:
        """在源文档中查找问题的答案"""
        if not self.client:
            return ""
        
        prompt = f"""
        Based on the following source text, answer this question briefly (1-2 sentences):
        
        Question: {question}
        
        Source Text:
        {source[:1000]}  # 限制长度
        
        Answer:
        """
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100
                )
                return response.choices[0].message.content.strip()
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
        except Exception as e:
            return ""
    
    def _extract_answer_from_faq(self, question: str, faq_answer: str) -> str:
        """从FAQ答案中提取对问题的回答"""
        # 简化版本：如果问题关键词在答案中，返回相关部分
        question_words = set(question.lower().split())
        answer_sentences = faq_answer.split('.')
        
        for sentence in answer_sentences:
            sentence_words = set(sentence.lower().split())
            if len(question_words.intersection(sentence_words)) >= 2:
                return sentence.strip()
        
        return faq_answer[:100]  # 返回前100字符
    
    def _calculate_consistency(self, faq_answer: str, source_answers: List[str], 
                              questions: List[str]) -> float:
        """计算FAQ答案与源文档答案的一致性"""
        if not self.client or not source_answers:
            return self._simple_similarity(faq_answer, ' '.join(source_answers))
        
        # 使用LLM评估一致性
        source_text = ' '.join([f"Q: {q}\nA: {a}" for q, a in zip(questions, source_answers)])
        
        prompt = f"""
        Rate the consistency between these two answers (0-10):
        
        FAQ Answer:
        {faq_answer}
        
        Source-based Answers:
        {source_text}
        
        Score (0-10, where 10 is completely consistent):
        """
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50
                )
                text = response.choices[0].message.content
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=50,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
            
            # 提取分数
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if score_match:
                score = float(score_match.group(1))
                return min(score / 10.0, 1.0)  # 转换为0-1范围
            
        except Exception as e:
            print(f"计算一致性失败: {str(e)}")
        
        return 0.5  # 默认分数
    
    def _compare_answers(self, source_answers: List[str], faq_answers: List[str]) -> float:
        """比较源文档答案和FAQ答案"""
        if not source_answers or not faq_answers:
            return 0.0
        
        # 简化版本：计算平均相似度
        similarities = []
        for s_ans, f_ans in zip(source_answers, faq_answers):
            sim = self._simple_similarity(s_ans, f_ans)
            similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """简单的词重叠相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _simple_consistency_check(self, faq: Dict, source_chunk: str) -> Dict:
        """简化的一致性检查（不使用LLM）"""
        # 基于关键词重叠
        answer_words = set(faq['answer'].lower().split())
        source_words = set(source_chunk.lower().split())
        
        overlap = answer_words.intersection(source_words)
        similarity = len(overlap) / len(answer_words) if answer_words else 0.0
        
        return {
            'method': 'Simple',
            'consistency_score': similarity,
            'is_consistent': similarity >= 0.3
        }


def evaluate_faqs_from_json(json_file: str, source_text: str = None, 
                           method: str = "qafacteval", sample_size: int = None):
    """
    从JSON文件评估FAQ质量
    
    Args:
        json_file: FAQ JSON文件路径
        method: 评估方法（qafacteval或questeval）
        sample_size: 评估的FAQ数量（如果为None或0，评估所有）
    """
    print(f"\n{'='*70}")
    print(f"评估文件: {json_file}")
    print(f"方法: {method}")
    print(f"{'='*70}")
    
    # 读取FAQ数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    faqs = data.get('faqs', [])
    print(f"总FAQ数: {len(faqs)}")
    
    # 抽样（如果需要）
    if sample_size and sample_size > 0 and sample_size < len(faqs):
        import random
        faqs = random.sample(faqs, sample_size)
        print(f"抽样评估: {len(faqs)} 个FAQ")
    else:
        print(f"全样本评估: {len(faqs)} 个FAQ")
    
    # 准备源文档（如果有）
    source_chunks = None
    if source_text:
        # 简单分块
        chunk_size = 500
        source_chunks = [source_text[i:i+chunk_size] 
                        for i in range(0, len(source_text), chunk_size)]
    
    # 初始化评估器
    evaluator = FAQEvaluator()
    
    # 评估每个FAQ
    results = []
    consistent_count = 0
    
    print(f"\n开始评估 {len(faqs)} 个FAQ...")
    print("这可能需要一些时间，请耐心等待...\n")
    
    for i, faq in enumerate(faqs):
        if (i + 1) % 10 == 0 or (i + 1) == len(faqs):
            print(f"  处理中: {i+1}/{len(faqs)} ({((i+1)/len(faqs)*100):.1f}%)")
        
        # 选择源文档块（如果有）
        source_chunk = ""
        if source_chunks:
            # 使用FAQ的chunk_id找到对应的源文档块
            chunk_id = faq.get('chunk_id', 0)
            if chunk_id < len(source_chunks):
                source_chunk = source_chunks[chunk_id]
            else:
                source_chunk = source_chunks[0]  # 默认使用第一个
        elif source_text:
            source_chunk = source_text[:1000]  # 使用前1000字符
        
        # 评估
        if method == "qafacteval":
            result = evaluator.qafacteval_method(faq, source_chunk)
        else:
            result = evaluator.questeval_method(faq, source_chunk)
        
        result['faq_index'] = i
        result['question'] = faq.get('question', '')[:80]
        result['answer'] = faq.get('answer', '')[:100]
        
        results.append(result)
        
        if result.get('is_consistent', False):
            consistent_count += 1
    
    # 统计
    consistency_scores = [r['consistency_score'] for r in results]
    avg_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
    consistency_rate = consistent_count / len(faqs) if faqs else 0
    
    print(f"\n评估结果:")
    print(f"  平均一致性分数: {avg_score:.3f}")
    print(f"  一致性比例 (>0.7): {consistency_rate:.1%}")
    print(f"  一致FAQ数: {consistent_count}/{len(faqs)}")
    
    # 保存结果
    output_file = json_file.replace('.json', '_evaluation.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'file': json_file,
            'method': method,
            'total_faqs': len(faqs),
            'average_consistency': avg_score,
            'consistency_rate': consistency_rate,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 结果已保存到: {output_file}")
    
    return {
        'average_consistency': avg_score,
        'consistency_rate': consistency_rate,
        'consistent_count': consistent_count,
        'total_count': len(faqs)
    }


def main():
    """主函数：评估所有JSON文件"""
    import sys
    
    print("="*70)
    print("📊 使用课程方法评估FAQ质量")
    print("="*70)
    print("\n方法说明:")
    print("1. QAFactEval: 从FAQ答案生成问题，在源文档中找答案，评估一致性")
    print("2. QuestEval: 双重验证，比较源文档和FAQ答案的一致性")
    print("\n注意: 如果没有API密钥，将使用简化的评估方法")
    
    # 查找所有JSON文件
    json_files = glob.glob('output/*.json')
    json_files = [f for f in json_files if '_evaluation' not in f]  # 排除评估结果文件
    
    if not json_files:
        print("\n❌ 未找到任何JSON文件！")
        return
    
    print(f"\n找到 {len(json_files)} 个JSON文件")
    
    # 从命令行参数获取方法，或使用默认值
    if len(sys.argv) > 1:
        method = sys.argv[1].lower()
        if method not in ['qafacteval', 'questeval']:
            print(f"⚠️  无效的方法: {method}，使用默认值: qafacteval")
            method = "qafacteval"
    else:
        method = "qafacteval"
        print(f"\n使用默认方法: {method}")
    
    # 从命令行参数获取样本大小，或使用默认值
    if len(sys.argv) > 2:
        try:
            sample_size_input = sys.argv[2].lower()
            if sample_size_input in ['all', 'full', 'none', '0']:
                sample_size = None  # 评估所有
                print(f"使用全样本评估（所有FAQ）")
            else:
                sample_size = int(sample_size_input)
                print(f"使用样本大小: {sample_size}")
        except ValueError:
            sample_size = None
            print(f"⚠️  无效的样本大小，使用全样本评估")
    else:
        sample_size = None
        print(f"使用全样本评估（所有FAQ）")
    
    print(f"\n开始评估...")
    print(f"⚠️  注意：全样本评估可能需要较长时间和更多API调用")
    
    # 评估每个文件
    all_results = []
    
    for json_file in sorted(json_files):
        try:
            result = evaluate_faqs_from_json(json_file, method=method, sample_size=sample_size)
            result['file'] = json_file
            all_results.append(result)
        except Exception as e:
            print(f"❌ 处理 {json_file} 时出错: {str(e)}")
    
    # 打印总结
    print("\n" + "="*70)
    print("📊 总体评估总结")
    print("="*70)
    
    for result in all_results:
        filename = Path(result['file']).stem
        print(f"\n{filename}:")
        print(f"  平均一致性: {result['average_consistency']:.3f}")
        print(f"  一致性比例: {result['consistency_rate']:.1%}")
        print(f"  一致FAQ: {result['consistent_count']}/{result['total_count']}")
    
    print("\n" + "="*70)
    print("✅ 评估完成！")
    print("="*70)
    print("\n💡 提示:")
    print("1. 查看详细的评估结果文件: output/*_evaluation.json")
    print("2. 一致性分数>0.7的FAQ被认为是高质量的")
    print("3. 可以结合手动验证来确认结果")


if __name__ == "__main__":
    main()

