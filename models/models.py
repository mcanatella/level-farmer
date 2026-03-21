from typing import List, Literal, Union

from pydantic import BaseModel


class StaticBounceParams(BaseModel):
    tick_size: float
    proximity_threshold: int
    reward_ticks: int
    risk_ticks: int
    tick_tolerance: int
    kind: Literal["static_bounce"] = "static_bounce"
    min_separation: int = 10
    top_n: int = 10
    decay_half_life_days: float = 15.0
    precision: int = 2


class StaticBounceWithDeltaParams(BaseModel):
    tick_size: float
    proximity_threshold: int
    reward_ticks: int
    risk_ticks: int
    tick_tolerance: int
    kind: Literal["static_bounce_with_delta"] = "static_bounce_with_delta"
    min_separation: int = 10
    top_n: int = 10
    decay_half_life_days: float = 15.0
    precision: int = 2
    delta_window_seconds: float = 300.0
    attempt_seconds: int = (
        30  # how long to wait for confirmation after price enters zone
    )
    delta_ratio_threshold: float = 0.20  # 20% imbalance by default
    min_response_ticks: int = 3  # prove bounce/rejection
    max_penetration_ticks: int = 4  # avoid "knife through level"
    cooldown_seconds: int = 120  # per-level cooldown to prevent spam on chop


StrategyParams = Union[StaticBounceParams, StaticBounceWithDeltaParams]


class CsvDataSource(BaseModel):
    kind: Literal["csv"] = "csv"
    data_dir: str
    symbols: List[str]
    pct_margin: float
    abs_margin: int
    min_total_volume: int


class ProjectXDataSource(BaseModel):
    kind: Literal["projectx"] = "projectx"
    base_url: str
    username: str
    api_key: str
    contract_id: str


DataSource = Union[CsvDataSource, ProjectXDataSource]


class AggregationParams(BaseModel):
    lookback_days: int
    data_source: DataSource
    candle_length: int = 5
    unit: str = "minutes"


class StrategyConfig(BaseModel):
    name: str
    aggregation_params: AggregationParams
    strategy_params: StrategyParams


class BacktestConfig(BaseModel):
    name: str
    dates: List[str]
    strategy: StrategyConfig


class BacktestResult(BaseModel):
    total_pnl: float
    trades_file: str
