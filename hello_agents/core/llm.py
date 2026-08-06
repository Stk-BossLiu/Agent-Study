import sys
from pathlib import Path

from .message import Message

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from typing import List, Optional
from openai import OpenAI
from main import HelloAgentsLLM
import os


class MyLLM(HelloAgentsLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: Optional[str] = "auto",
        **kwargs
    ):

        if provider == "modelscope":
            print("注册modelsope服务")
            self.provider = "modelscope"
            self.api_key = os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://api-inference.modelscope.cn/v1/"

            if not self.api_key:
                raise ValueError("MODELSCOPE_API_KEY is not set")
            self.model = model or os.getenv("LLM_MODEL_ID") or "deepseek-v4-flash"
            self.temperature = kwargs.get("temperature", 0.7)
            self.max_tokens = kwargs.get("max_tokens")
            self.timeout = kwargs.get("timeout", 60)

            self.client = OpenAI(
                api_key=self.api_key, base_url=self.base_url, timeout=self.timeout
            )
        else:
            super().__init__(model=model, base_url=base_url, api_key=api_key)
