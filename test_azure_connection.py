import os, inspect
from openai import AzureOpenAI


# 1. 获取环境变量
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
# 如果你刚才没配这个变量，这里手动填 "gpt-5-chat"
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5.2") 

print(f"正在测试连接 -> {endpoint}")
print(f"使用模型(部署名) -> {deployment}")

try:
    # 2. 初始化客户端
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-12-01-preview"
    )

    # test
    sig = inspect.signature(client.chat.completions.create)

    print(f"{'='*20} API 参数列表 {'='*20}")
    for name, param in sig.parameters.items():
        # 过滤掉 self 和 kwargs，打印具体参数
        if name not in ['self', 'kwargs']:
            default = param.default if param.default != inspect.Parameter.empty else "Required"
            print(f"🔹 {name:<25} (Default: {default})")

    


    # 3. 发送测试请求
    response = client.chat.completions.create(
        model=deployment, # Azure 中这里填 Deployment Name
        messages=[
            {"role": "user", "content": "Hello! result = 1 + 1. Reply only the result."}
        ]
    )

    # 4. 输出结果
    print("\n✅ 测试成功！")
    print("模型回复:", response.choices[0].message.content)

except Exception as e:
    print("\n❌ 测试失败")
    print("错误信息:", e)