import os
from pydantic import BaseModel
from typing import Optional


class Config(BaseModel):

    default_model: str = "Qwen/Qwen3.5-35B-A3B"
    default_provider: str = "modelscope"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    debug: bool = False
    log_level: str = "INFO"

    max_history_length: int = 100

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            debug=os.getenv("DEBUG", "false"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "None")),
        )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
