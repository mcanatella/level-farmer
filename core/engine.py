from .protocols import AsyncTicker, Ticker
from .types import Tick
from typing import Any, Awaitable, Callable, Dict

import asyncio
import logging


async def run_engine_async(
    ticker: AsyncTicker,
    logger: logging.Logger,
    state: Dict[str, Any],
    on_tick: Callable[[Tick, logging.Logger, Dict[str, Any]], Awaitable[None] | None],
):
    async for tick in ticker:
        res = on_tick(tick, logger, state)
        if asyncio.iscoroutine(res):
            await res


def run_engine(
    ticker: Ticker,
    logger: logging.Logger,
    state: Dict[str, Any],
    ontick: Callable[[Tick, logging.Logger, Dict[str, Any]], None],
) -> None:
    for tick in ticker:
        ontick(tick, logger, state)
