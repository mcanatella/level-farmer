from config import (
    BacktestSettings,
    init_backtest_logger,
)
from datetime import datetime

import argparse
import asyncio

from api import (
    StaticBounceParams,
    BacktestRequest,
    run_static_bounce_async,
)
from pathlib import Path


async def main(args) -> None:
    settings = BacktestSettings.build(args)

    logger = init_backtest_logger()

    # Parse string version of the back test date into a date object
    d = datetime.strptime(settings.backtest_date, "%Y%m%d").date()

    params = StaticBounceParams(
        kind="static_bounce",
        proximity_threshold=0.03,
        reward_points=0.20,
        risk_points=0.10,
        price_tolerance=settings.price_tolerance,
        min_separation=settings.min_separation,
        top_n=settings.top_n,
        decay_half_life_days=15.0,
    )

    request = BacktestRequest(
        data_dir=Path(settings.data_dir),
        backtest_date=d,
        symbols=settings.symbols,
        lookback_days=settings.days,
        candle_length=settings.candle_length,
        unit=settings.unit,
        params=params,
    )

    result = await run_static_bounce_async(request, logger)

    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tunable support and resistance level finder"
    )
    BacktestSettings.set_args(parser)
    args = parser.parse_args()

    asyncio.run(main(args))
