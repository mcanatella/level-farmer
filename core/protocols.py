from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Dict, Iterator, Protocol

if TYPE_CHECKING:
    from tickers.state import TickerState

    from .types import Signal, Tick


# Pseudo interface for anything that can stream tick objects synchronously
class Ticker(Protocol):
    def __iter__(self) -> Iterator[Tick]: ...


# Pseudo interface for anything that can stream tick objects asynchronously
class AsyncTicker(Protocol):
    def __aiter__(self) -> AsyncIterator[Tick]: ...


# Pseudo interface for anything that can aggregate candles
class Aggregator(Protocol):
    def get_candles(self) -> list[Dict[str, Any]]: ...


# Pseudo interface for anything that can implement a trading strategy
class Strategy(Protocol):
    def check(self, tick: Tick, **kwargs: Any) -> Signal | None: ...
    def get_backtest_handler(
        self,
    ) -> Callable[[Tick, logging.Logger, TickerState], None]: ...
    def get_live_handler(
        self,
    ) -> Callable[[Tick, logging.Logger, TickerState], None]: ...
