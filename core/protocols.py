from .types import Tick
from typing import AsyncIterator, Protocol


# Pseudo interface for anything that can stream tick objects asynchronously
class Ticker(Protocol):
    def __aiter__(self) -> AsyncIterator[Tick]: ...
