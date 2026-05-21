import logging
from typing import Any, Callable

from core import Signal, Tick
from tickers.state import TickerState


class Dummy:
    def __init__(self):
        pass

    def check(self, tick: Tick, **kwargs: Any) -> Signal | None:
        pass

    def get_backtest_handler(
        self,
    ) -> Callable[[Tick, logging.Logger, TickerState], None]:
        return dummy_handler

    def get_live_handler(self) -> Callable[[Tick, logging.Logger, TickerState], None]:
        return dummy_handler

    def reset(self) -> None:
        pass


def dummy_handler(tick: Tick, logger: logging.Logger, state: TickerState) -> None:
    pass
