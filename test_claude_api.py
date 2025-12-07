"""
Test Anthropic Claude API connectivity
"""

import os
import sys

print("="*60)
print("🔍 Claude API连接测试")
print("="*60)

# Check API key
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("\n❌ 错误：Anthropic API密钥未设置！")
    print("\n步骤：")
    print("1. 访问：https://console.anthropic.com/")
    print("2. 注册账号（新用户有$5免费额度）")
    print("3. 获取API密钥")
    print("\n然后运行：")
    print("export ANTHROPIC_API_KEY='sk-ant-你的密钥'")
    sys.exit(1)

print(f"\n✓ API密钥已设置: {api_key[:20]}...")

# Test Anthropic API
print("\n📡 测试Claude API连接...")

try:
    from anthropic import Anthropic
    
    client = Anthropic(api_key=api_key)
    
    # Simple test call
    print("   发送测试请求...")
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=50,
        messages=[
            {"role": "user", "content": "Say 'Claude API test successful' in one sentence."}
        ]
    )
    
    result = response.content[0].text
    print(f"   ✓ 响应: {result}")
    print("\n✅ Claude API连接成功！")
    print("\n🎉 你可以使用Claude来生成FAQs了！")
    print("\n💰 新用户有$5免费额度，足够完成项目！")
    
except Exception as e:
    print(f"\n❌ API调用失败！")
    print(f"\n错误信息：{str(e)}")
    print("\n请检查：")
    print("1. API密钥是否正确")
    print("2. 是否已注册Anthropic账号")
    print("3. 网络连接是否正常")
    sys.exit(1)

print("="*60)

