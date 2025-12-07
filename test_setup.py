"""
Quick test to check if everything is set up correctly
"""

import os
import sys

print("="*60)
print("🔧 FAQ Generator - 环境检查")
print("="*60)

# 1. Check Python version
print(f"\n✓ Python版本: {sys.version.split()[0]}")

# 2. Check API keys
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

if openai_key:
    print(f"✓ OpenAI API Key: 已设置 ({openai_key[:10]}...)")
else:
    print("⚠️  OpenAI API Key: 未设置")
    print("   请运行: export OPENAI_API_KEY='your-key-here'")

if anthropic_key:
    print(f"✓ Anthropic API Key: 已设置 ({anthropic_key[:10]}...)")
else:
    print("⚠️  Anthropic API Key: 未设置")
    print("   请运行: export ANTHROPIC_API_KEY='your-key-here'")

# 3. Check test documents
print("\n📄 测试文档:")
test_docs = [
    'test_documents/ISE-547_Syllabus.docx',
    'test_documents/art-science-GenAI.pdf',
    'test_documents/pandas.pdf',
    'test_documents/Student-Handbook-2025-2026.pdf'
]

for doc in test_docs:
    if os.path.exists(doc):
        size = os.path.getsize(doc) / 1024  # KB
        print(f"  ✓ {os.path.basename(doc)} ({size:.0f} KB)")
    else:
        print(f"  ✗ {os.path.basename(doc)} (未找到)")

# 4. Check output directory
if not os.path.exists('output'):
    os.makedirs('output')
    print("\n✓ 创建output文件夹")
else:
    print("\n✓ output文件夹已存在")

print("\n" + "="*60)

if openai_key or anthropic_key:
    print("🎉 环境检查完成！可以开始运行测试。")
    print("\n建议命令：")
    print("python main.py --input test_documents/ISE-547_Syllabus.docx --output test_faqs --verbose")
else:
    print("⚠️  请先设置API密钥！")
    print("\n快速设置方法：")
    print("export OPENAI_API_KEY='sk-proj-your-key-here'")

print("="*60)

