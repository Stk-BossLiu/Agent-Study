import os
from openai import OpenAI, Stream
from dotenv import load_dotenv
from typing import List, Dict
from openai.types.chat import ChatCompletionChunk
from serpapi import Client

load_dotenv()


class HelloAgentsLLM:
    def __init__(self, model: str, base_url: str, api_key: str, timeout: int = 60):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        print(f"Sending request to {self.base_url} with model {self.model}")
        try:
            response: Stream[ChatCompletionChunk] = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            collected_contents = []  # 字符串数组
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_contents.append(content)
            print()
            return "".join(collected_contents)

        except Exception as e:
            print(f"发生错误: {e}")
            return None


if __name__ == "__main__":
    try:
        client = HelloAgentsLLM(
            model=os.getenv("LLM_MODEL_ID"),
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
        )
        user_input = input("Enter your message: ")
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that writes Python code.",
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]
        response = client.chat(messages)
        print("response: ", response)
    except Exception as e:
        print(f"发生错误: {e}")
