from abc import ABC, abstractmethod

from typing import Optional, List
from .config import Config
from .message import Message
from main import HelloAgentsLLM


class Agent(ABC):
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self.history: List[Message] = []

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        pass

    def add_message(self, message: Message) -> None:
        self.history.append(message)

    def clear_history(self) -> None:
        self.history = []

    def get_history(self) -> List[Message]:
        return self.history.copy()

    def __str__(self) -> str:
        return f"Agent(name={self.name}, provider={self.llm.provider})"
