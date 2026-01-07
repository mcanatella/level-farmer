import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from aggregators import CsvAggregator
from core import Strategy, run_engine_async
from strategies import StaticBounce
from tickers import CsvTicker

from .handlers import static_bounce_handler


@dataclass(frozen=True)
class StaticBounceParams:
    kind: Literal["static_bounce"] = "static_bounce"
    tick_size: float = 0.01
    proximity_threshold: int = 3
    reward_ticks: int = 20
    risk_ticks: int = 10
    tick_tolerance: int = 5
    min_separation: int = 10
    top_n: int = 5
    decay_half_life_days: float = 15.0


# TODO: To be implemented; primarily an example right now
@dataclass(frozen=True)
class VwapFadeParams:
    kind: Literal["vwap_fade"] = "vwap_fade"
    entry_band: float = 0.5
    stop_band: float = 1.0


StrategyParams = Union[StaticBounceParams, VwapFadeParams]


@dataclass(frozen=True)
class CsvDataSource:
    kind: Literal["csv"] = "csv"
    data_dir: Path
    symbols: List[str]


@dataclass(frozen=True)
class ProjectXDataSource:
    kind: Literal["projectx"] = "projectx"
    base_url: str
    username: str
    api_key: str
    contract_id: str


DataSource = Union[CsvDataSource, ProjectXDataSource]


@dataclass(frozen=True)
class BacktestRequest:
    backtest_date: date
    lookback_days: int = 10
    candle_length: int = 5
    unit: str = "minutes"
    data_source: DataSource = field(default_factory=CsvDataSource)
    params: StrategyParams = field(default_factory=StaticBounceParams)


@dataclass(frozen=True)
class BacktestResult:
    total_pnl: float
    trades_file: Path


def _build_strategy(
    params: StrategyParams, logger: logging.Logger, candles: List[dict]
) -> Strategy:
    if params.kind == "static_bounce":
        return StaticBounce(
            logger,
            candles,
            params.tick_size,
            params.proximity_threshold,
            params.reward_ticks,
            params.risk_ticks,
            params.tick_tolerance,
            params.min_separation,
            params.top_n,
            params.decay_half_life_days,
        )
    elif params.kind == "vwap_fade":
        raise NotImplementedError("VWAP Fade strategy not implemented")
    else:
        raise ValueError(f"Unsupported strategy kind: {params.kind}")


async def run_static_bounce_async(
    req: BacktestRequest,
    logger: Optional[logging.Logger] = None,
) -> BacktestResult:
    if logger is None:
        logger = logging.getLogger("backtest_runner")

    start_date = req.backtest_date - timedelta(days=req.lookback_days)
    end_date = req.backtest_date - timedelta(days=1)

    # Build a list of historical candles over the specified time window via CsvAggregator
    aggregator = CsvAggregator(
        logger,
        req.data_dir,
        start_date,
        end_date,
        req.symbols,
        candle_length=req.candle_length,
        unit=req.unit,
    )
    candles = aggregator.get_candles()

    # Initialize requested strategy
    strategy = _build_strategy(req.params, logger, candles)

    # Initialize handler state
    state: Dict[str, Any] = {
        "total_pnl": 0.0,
        "position": None,
        "strategy": strategy,
    }

    print(type(req.data_dir))

    trades_file = req.data_dir / f"glbx-mdp3-{req.backtest_date:%Y%m%d}.trades.csv"
    ticker = CsvTicker(str(trades_file), req.symbols)

    await run_engine_async(ticker, logger, state, static_bounce_handler)

    return BacktestResult(
        total_pnl=state["total_pnl"],
        trades_file=trades_file,
    )
