from groq import Groq
try:
    client = Groq(api_key="gsk_invalidKEY12345678901234567890123456789")
    client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "hi"}],
        stream=False
    )
except Exception as e:
    print(str(e))
