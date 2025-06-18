from abc import ABC, abstractmethod
from typing import Sequence, Any

from .tool import Tool

class Agent(ABC):
    tools: Sequence[Tool]
    model: Any  # LLM backend wrapper

    @abstractmethod
    def run(self, prompt: str, **kwargs) -> Any:
        """
        core agent pipeline: plan → tool selection → execute → loop/return
        """
        raise NotImplementedError
