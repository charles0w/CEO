from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def send(self, message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> str:
        raise NotImplementedError
