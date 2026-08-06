from dotenv import load_dotenv
from core.llm import MyLLM
import os

load_dotenv()

llm = MyLLM(
    provider="modelscope",
    model="Qwen/Qwen3.5-35B-A3B",
    api_key=os.getenv("MODELSCOPE_API_KEY"),
    base_url=os.getenv("MODELSCOPE_BASE_URL"),
)

messages = [{"role": "user", "content": f"{input("请输入问题：")}"}]
print("=" * 20 + "Response" + "=" * 20)
response_stream = llm.chat(messages)
