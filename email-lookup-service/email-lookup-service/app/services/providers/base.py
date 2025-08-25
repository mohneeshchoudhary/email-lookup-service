from abc import ABC, abstractmethod
from typing import Optional

class Provider(ABC):
    name: str

    @abstractmethod
    async def lookup(self, *, username: str, **kwargs) -> Optional[str]:
        ...
