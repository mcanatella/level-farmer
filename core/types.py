from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Tick:
    t: datetime
    price: float
    size: int
    side: str
    symbol: str

    def delta(self) -> int:
        if self.side == "B":
            return self.size

        if self.side == "A":
            return -self.size

        return 0
