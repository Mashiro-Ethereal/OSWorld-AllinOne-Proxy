import os
import sys
import base64

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: The 'anthropic' python package is required.")
    print("Install it by running: pip install anthropic")
    sys.exit(1)

def test_opus():
    # Attempt to get the API key and base URL from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY", "sk-lmhub-9f73a3a1fae7bbf55f5d14745e648efe")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY is not set. Please set it before running the script.")
        print("Example: export ANTHROPIC_API_KEY='your_api_key_here'")

    # Using the exact model name from the user's provided export commands
    model_name = os.environ.get("ANTHROPIC_DEFAULT_OPUS_MODEL", "bedrock-opus-4.6")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://inference.willow.zip")
    
    print(f"Testing Model: {model_name}")
    print(f"Base URL: {base_url}")
    print("-" * 40)

    try:
        # Initialize the Anthropic client explicitly with the parsed variables
        client = Anthropic(api_key=api_key, base_url=base_url)
        
        # Send a simple message to test
        with open("/home/zhangxiuhui/projects/OSWorld/results-01201005/pyautogui/screenshot/gpt-5/chrome/0d8b7de3-e8de-4d86-b9fd-dd2dce58a217/step_0.png", "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "这张图片的内容是什么"
                        }
                    ]
                }
            ]
        )
        
        print("Success! API is working.")
        print("Response:")
        print(message.content[0].text)

    except Exception as e:
        import traceback
        print("Failed to connect or get response.")
        print(f"Error: {e}")
        traceback.print_exc()
        if hasattr(e, 'response'):
            print(f"Response status code: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"Response text: {getattr(e.response, 'text', 'N/A')}")

if __name__ == "__main__":
    test_opus()
