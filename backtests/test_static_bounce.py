import asyncio
import math
from datetime import date
from pathlib import Path
from typing import List

import pytest
from tabulate import tabulate

from api import (
    BacktestRequest,
    BacktestResult,
    StaticBounceParams,
    run_static_bounce_async,
)
from config import init_null_logger


def run_static_bounce_backtest(
    data_dir: Path,
    backtest_date: date,
    symbols: List[str],
    proximity_threshold: int = 3,
    reward_ticks: int = 20,
    risk_ticks: int = 10,
    tick_tolerance: int = 5,
    min_separation: int = 10,
    top_n: int = 5,
    decay_half_life_days: float = 15.0,
    lookback_days: int = 10,
) -> BacktestResult:
    """
    Sync wrapper so tests can stay non-async.
    """
    logger = init_null_logger()

    params = StaticBounceParams(
        kind="static_bounce",
        proximity_threshold=proximity_threshold,
        reward_ticks=reward_ticks,
        risk_ticks=risk_ticks,
        tick_tolerance=tick_tolerance,
        min_separation=min_separation,
        top_n=top_n,
        decay_half_life_days=decay_half_life_days,
    )

    req = BacktestRequest(
        data_dir=data_dir,
        backtest_date=backtest_date,
        symbols=symbols,
        lookback_days=lookback_days,
        candle_length=5,
        unit="minutes",
        params=params,
    )

    return asyncio.run(run_static_bounce_async(req, logger))


@pytest.mark.parametrize(
    "backtest_date",
    [
        date(2025, 12, 1),
        date(2025, 12, 2),
        date(2025, 12, 3),
        date(2025, 12, 4),
        date(2025, 12, 5),
        date(2025, 12, 7),
        date(2025, 12, 8),
        date(2025, 12, 9),
        date(2025, 12, 10),
        date(2025, 12, 11),
        date(2025, 12, 12),
        date(2025, 12, 14),
    ],
    ids=lambda d: d.strftime("%Y%m%d"),
)
@pytest.mark.parametrize(
    "proximity_threshold,reward_ticks,risk_ticks,tick_tolerance,"
    "min_separation,top_n,decay_half_life_days,lookback_days",
    [
        pytest.param(
            3,  # proximity_threshold
            20,  # reward_ticks
            10,  # risk_ticks
            5,  # tick_tolerance
            10,  # min_separation
            10,  # top_n
            15.0,  # decay_half_life_days
            10,  # lookback_days
            id="baseline",
        ),
    ],
)
def test_static_bounce(
    backtest_date: date,
    proximity_threshold: int,
    reward_ticks: int,
    risk_ticks: int,
    tick_tolerance: int,
    min_separation: int,
    top_n: int,
    decay_half_life_days: float,
    lookback_days: int,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "cl_historical"
    symbols = ["CLZ5", "CLF6"]

    res = run_static_bounce_backtest(
        data_dir=data_dir,
        backtest_date=backtest_date,
        symbols=symbols,
        proximity_threshold=proximity_threshold,
        reward_ticks=reward_ticks,
        risk_ticks=risk_ticks,
        tick_tolerance=tick_tolerance,
        min_separation=min_separation,
        top_n=top_n,
        decay_half_life_days=decay_half_life_days,
        lookback_days=lookback_days,
    )

    # Basic sanity assertions
    assert isinstance(res, BacktestResult)
    assert math.isfinite(res.total_pnl)

    # Print a one-row table so you can compare PnL across params
    row = [
        proximity_threshold,
        reward_ticks,
        risk_ticks,
        tick_tolerance,
        min_separation,
        top_n,
        round(res.total_pnl, 2),
    ]
    headers = [
        "prox_thresh",
        "reward",
        "risk",
        "tick_tol",
        "min_sep",
        "top_n",
        "PnL",
    ]

    print()
    print(tabulate([row], headers=headers, tablefmt="pretty"))
