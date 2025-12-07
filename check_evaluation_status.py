"""
检查评估进度和状态
"""

import json
import glob
import os
from pathlib import Path
from datetime import datetime

def check_evaluation_status():
    """检查评估状态"""
    print("="*70)
    print("🔍 评估状态检查")
    print("="*70)
    
    # 查找所有评估结果文件
    eval_files = glob.glob('output/*_evaluation.json')
    eval_files = [f for f in eval_files if 'analysis_report' not in f]
    
    # 查找所有原始FAQ文件
    faq_files = glob.glob('output/*_faqs_*.json')
    faq_files = [f for f in faq_files if 'evaluation' not in f and 'analysis_report' not in f]
    
    print(f"\n找到 {len(faq_files)} 个FAQ文件，{len(eval_files)} 个评估结果文件\n")
    
    # 检查每个文件的状态
    status = []
    
    for faq_file in sorted(faq_files):
        # 解析文件名
        faq_path = Path(faq_file)
        faq_name = faq_path.stem
        
        # 查找对应的评估文件
        eval_file = faq_file.replace('.json', '_evaluation.json')
        
        if os.path.exists(eval_file):
            # 读取评估结果
            try:
                with open(eval_file, 'r', encoding='utf-8') as f:
                    eval_data = json.load(f)
                
                # 读取原始FAQ
                with open(faq_file, 'r', encoding='utf-8') as f:
                    faq_data = json.load(f)
                
                total_faqs = faq_data.get('total_faqs', 0)
                evaluated_faqs = eval_data.get('total_faqs', 0)
                
                # 检查文件修改时间
                eval_mtime = os.path.getmtime(eval_file)
                eval_time = datetime.fromtimestamp(eval_mtime)
                time_ago = datetime.now() - eval_time
                
                # 判断状态
                if evaluated_faqs == total_faqs:
                    status_icon = "✅"
                    status_text = "完成"
                elif evaluated_faqs > 0:
                    status_icon = "🟡"
                    status_text = f"进行中 ({evaluated_faqs}/{total_faqs})"
                else:
                    status_icon = "❌"
                    status_text = "未开始"
                
                status.append({
                    'name': faq_name,
                    'total': total_faqs,
                    'evaluated': evaluated_faqs,
                    'status': status_text,
                    'icon': status_icon,
                    'time': eval_time,
                    'time_ago': time_ago,
                    'progress': evaluated_faqs / total_faqs * 100 if total_faqs > 0 else 0
                })
                
            except Exception as e:
                status.append({
                    'name': faq_name,
                    'total': '?',
                    'evaluated': '?',
                    'status': f'错误: {str(e)[:30]}',
                    'icon': '❌',
                    'time': None,
                    'time_ago': None,
                    'progress': 0
                })
        else:
            status.append({
                'name': faq_name,
                'total': '?',
                'evaluated': 0,
                'status': '未开始',
                'icon': '❌',
                'time': None,
                'time_ago': None,
                'progress': 0
            })
    
    # 打印状态表格
    print(f"{'文件':<30} {'状态':<20} {'进度':<15} {'最后更新':<20}")
    print("-"*70)
    
    for s in status:
        progress_bar = ""
        if isinstance(s['progress'], (int, float)):
            progress_bar = f"{s['progress']:.1f}%"
            if s['progress'] == 100:
                progress_bar = "100% ✅"
        
        time_str = ""
        if s['time']:
            if s['time_ago'].total_seconds() < 60:
                time_str = f"{int(s['time_ago'].total_seconds())}秒前"
            elif s['time_ago'].total_seconds() < 3600:
                time_str = f"{int(s['time_ago'].total_seconds()/60)}分钟前"
            else:
                time_str = s['time'].strftime("%H:%M:%S")
        
        print(f"{s['name']:<30} {s['icon']} {s['status']:<18} {progress_bar:<15} {time_str:<20}")
    
    # 总体统计
    print("\n" + "-"*70)
    completed = sum(1 for s in status if s['status'] == '完成')
    in_progress = sum(1 for s in status if '进行中' in s['status'])
    not_started = sum(1 for s in status if s['status'] == '未开始')
    
    print(f"✅ 已完成: {completed}/{len(status)}")
    print(f"🟡 进行中: {in_progress}/{len(status)}")
    print(f"❌ 未开始: {not_started}/{len(status)}")
    
    # 检查是否有进程在运行
    print("\n" + "="*70)
    print("🔍 检查评估进程")
    print("="*70)
    
    import subprocess
    try:
        # 检查是否有Python进程在运行评估脚本
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True
        )
        
        if 'evaluate_with_course_methods.py' in result.stdout:
            print("✅ 评估脚本正在运行中...")
            # 提取进程信息
            lines = [l for l in result.stdout.split('\n') if 'evaluate_with_course_methods.py' in l]
            for line in lines[:3]:  # 只显示前3个
                parts = line.split()
                if len(parts) > 1:
                    print(f"   进程ID: {parts[1]}")
        else:
            print("ℹ️  未检测到运行中的评估进程")
            if completed == len(status):
                print("✅ 所有评估已完成！")
            elif in_progress > 0:
                print("⚠️  有未完成的评估，但进程已停止")
                print("   可能原因：")
                print("   1. 评估已完成但状态未更新")
                print("   2. 进程被中断")
                print("   3. 评估遇到错误")
    except Exception as e:
        print(f"⚠️  无法检查进程状态: {str(e)}")
    
    print("\n" + "="*70)
    print("💡 提示:")
    print("   - 如果显示'完成'且进度100%，说明该文件评估已完成")
    print("   - 如果显示'进行中'，说明正在评估")
    print("   - 如果'最后更新'时间在变化，说明正在处理")
    print("   - 运行此脚本多次可以查看进度变化")
    print("="*70)


if __name__ == "__main__":
    check_evaluation_status()

