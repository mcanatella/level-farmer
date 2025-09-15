from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Tick:
    t: datetime
    price: float
    size: int
    side: str
    symbol: str
