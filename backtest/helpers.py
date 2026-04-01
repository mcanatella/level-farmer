import logging

from aggregators import CsvAggregator, ProjectXAggregator
from api.models import StrategyConfig
from core import Aggregator, Strategy
from datetime import datetime, timedelta
from projectx_client import Auth, MarketData
from strategies import MeanReversionEma, StaticBounce, StaticBounceWithDelta
from typing import List, Dict, Any


def build_aggregator(
    strategy_conf: StrategyConfig, logger: logging.Logger
) -> Aggregator:
    aggregator: Aggregator
    if strategy_conf.aggregation_params.data_source.kind == "projectx":
        auth = Auth(
            base_url=strategy_conf.aggregation_params.data_source.base_url,
            username=strategy_conf.aggregation_params.data_source.username,
            api_key=strategy_conf.aggregation_params.data_source.api_key,
        )
        jwt_token = auth.login()
        market_data_client = MarketData(
            strategy_conf.aggregation_params.data_source.base_url, jwt_token
        )
        aggregator = ProjectXAggregator(
            logger, strategy_conf.aggregation_params, market_data_client
        )
    elif strategy_conf.aggregation_params.data_source.kind == "csv":
        today = datetime.now().date()
        start_date = today - timedelta(
            days=strategy_conf.aggregation_params.lookback_days
        )
        aggregator = CsvAggregator(
            logger, strategy_conf.aggregation_params, start_date, today
        )
    else:
        raise ValueError(
            f"Unsupported data_source: {strategy_conf.aggregation_params.data_source.kind}"
        )

    return aggregator

def build_strategy(
    config: StrategyConfig, logger: logging.Logger, candles: List[Dict[str, Any]]
) -> Strategy:
    if config.strategy_params.kind == "static_bounce":
        return StaticBounce(logger, candles, config.strategy_params)
    elif config.strategy_params.kind == "static_bounce_with_delta":
        return StaticBounceWithDelta(logger, candles, config.strategy_params)
    elif config.strategy_params.kind == "mean_reversion_ema":
        return MeanReversionEma(logger, candles, config.strategy_params)
    else:
        raise ValueError(f"Unsupported strategy kind: {config.strategy_params.kind}")