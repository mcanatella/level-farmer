import argparse
import logging

from aggregators import CsvAggregator, ProjectXAggregator
from config import FarmSettings, init_strucutred_logger
from core import Aggregator, Strategy
from datetime import datetime, timedelta
from models import StrategyConfig
from projectx_client import Auth, MarketData
from typing import Any, Dict, List
from strategies import MeanReversionEma, StaticBounce, StaticBounceWithDelta

# TODO: implement somewhere common since this is duplicated in discover.py and runner.py
def _build_aggregator(strategy_conf: StrategyConfig, logger: logging.Logger) -> Aggregator:
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

# TODO: implement somewhere common since this is duplicated in discover.py and runner.py
def _build_strategy(
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

def main(args):
    logger = init_strucutred_logger()

    settings = FarmSettings.build(args)

    # Look up the specified strategy in settings and raise an error if not present
    strategy_conf = None
    for s in settings.strategies:
        if s.name == args.strategy:
            strategy_conf = s
            break
    if strategy_conf is None:
        raise ValueError(f"Strategy '{args.strategy}' not found in configuration")
    
    aggregator = _build_aggregator(strategy_conf, logger)

    strategy = _build_strategy(strategy_conf, logger, aggregator.get_candles())

    print(strategy)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Modular quant trading bot",
    )
    FarmSettings.set_args(parser)
    args = parser.parse_args()

    main(args)
