import argparse
from datetime import datetime, timedelta

from aggregators import CsvAggregator, ProjectXAggregator
from config import DiscoverSettings, init_backtest_logger
from core import Aggregator
from projectx_client import Auth, MarketData
from strategies import StaticBounce


def main(args) -> None:
    logger = init_backtest_logger()

    settings = DiscoverSettings.build(args)

    # Look up the specified strategy in settings and raise an error if not present
    strategy_query = None
    for s in settings.strategies:
        if s.name == args.strategy:
            strategy_query = s
            break
    if strategy_query is None:
        raise ValueError(f"Strategy '{args.strategy}' not found in configuration")

    aggregator: Aggregator
    if strategy_query.aggregation_params.data_source.kind == "projectx":
        auth = Auth(
            base_url=strategy_query.aggregation_params.data_source.base_url,
            username=strategy_query.aggregation_params.data_source.username,
            api_key=strategy_query.aggregation_params.data_source.api_key,
        )
        jwt_token = auth.login()
        market_data_client = MarketData(
            strategy_query.aggregation_params.data_source.base_url, jwt_token
        )

        aggregator = ProjectXAggregator(
            logger,
            market_data_client,
            strategy_query.aggregation_params.data_source.contract_id,
            strategy_query.aggregation_params.lookback_days,
            strategy_query.aggregation_params.candle_length,
            unit=strategy_query.aggregation_params.unit,
        )
    elif strategy_query.aggregation_params.data_source.kind == "csv":
        today = datetime.now().date()
        start_date = today - timedelta(
            days=strategy_query.aggregation_params.lookback_days
        )

        aggregator = CsvAggregator(
            logger,
            strategy_query.aggregation_params.data_source.data_dir,
            start_date,
            today,
            strategy_query.aggregation_params.data_source.symbols,
            candle_length=strategy_query.aggregation_params.candle_length,
            unit=strategy_query.aggregation_params.unit,
        )
    else:
        raise ValueError(
            f"Unsupported data_source: {strategy_query.aggregation_params.data_source.kind}"
        )

    strategy = StaticBounce(
        logger,
        aggregator.get_candles(),
        strategy_query.strategy_params.tick_size,
        strategy_query.strategy_params.proximity_threshold,  # proximity_threshold unused when simply discovering signal data
        strategy_query.strategy_params.reward_ticks,  # reward_ticks unused when simply discovering signal data
        strategy_query.strategy_params.risk_ticks,  # risk_ticks unused when simply discovering signal data
        strategy_query.strategy_params.tick_tolerance,
        strategy_query.strategy_params.min_separation,
        strategy_query.strategy_params.top_n,
        strategy_query.strategy_params.decay_half_life_days,
    )

    strategy.print_static_levels()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tunable support and resistance level finder"
    )
    DiscoverSettings.set_args(parser)
    args = parser.parse_args()

    main(args)
