from unittest.mock import patch
from groq import Groq

def test_groq():
    client = Groq(api_key="test_key")
    
    with patch("groq._base_client.SyncAPIClient._request") as mock_request:
        try:
            client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": "hi"}],
                stream=False
            )
        except Exception as e:
            pass
            
        print("Mock called with:")
        for call in mock_request.call_args_list:
            print(call.kwargs.get("options", {}).get("json", {}).get("model"))

test_groq()
