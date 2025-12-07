"""
Test API connectivity
"""

import os
import sys

print("="*60)
print("🔍 API连接测试")
print("="*60)

# Check API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("\n❌ 错误：OpenAI API密钥未设置！")
    print("\n请在终端运行：")
    print("export OPENAI_API_KEY='sk-proj-你的密钥'")
    sys.exit(1)

print(f"\n✓ API密钥已设置: {api_key[:20]}...")

# Test OpenAI API
print("\n📡 测试OpenAI API连接...")

try:
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key)
    
    # Simple test call
    print("   发送测试请求...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'API test successful' in one sentence."}
        ],
        max_tokens=50
    )
    
    result = response.choices[0].message.content
    print(f"   ✓ 响应: {result}")
    print("\n✅ API连接成功！")
    print("\n🎉 你的环境配置正确，可以正常使用！")
    
except Exception as e:
    print(f"\n❌ API调用失败！")
    print(f"\n错误信息：{str(e)}")
    print("\n可能的原因：")
    print("1. API密钥无效或过期")
    print("2. 账户余额不足")
    print("3. 网络连接问题")
    print("\n解决方法：")
    print("1. 检查API密钥是否正确：https://platform.openai.com/api-keys")
    print("2. 检查账户余额：https://platform.openai.com/account/billing/overview")
    print("3. 检查网络连接")
    sys.exit(1)

print("="*60)

