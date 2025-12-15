from aggregators import ProjectXAggregator, CsvAggregator
from config import DiscoverSettings, init_backtest_logger
from core import Aggregator
from datetime import datetime, timedelta
from projectx_client import Auth, MarketData
from strategies import StaticBounce

import argparse


def main(args) -> None:
    logger = init_backtest_logger()

    settings = DiscoverSettings.build(args)
    settings.validate()

    aggregator: Aggregator
    if settings.data_source == "projectx":
        auth = Auth(
            base_url=settings.api.base, username=settings.api.user, api_key=settings.api.key
        )
        jwt_token = auth.login()
        market_data_client = MarketData(settings.api.base, jwt_token)

        aggregator = ProjectXAggregator(
            logger,
            market_data_client,
            settings.api.contract_id,
            days=settings.days,
            candle_length=settings.candle_length,
            unit=settings.unit,
        )
    elif settings.data_source == "csv":
        today = datetime.now().date()
        start_date = today - timedelta(days=args.days)

        aggregator = CsvAggregator(
            logger,
            settings.data_directory,
            start_date,
            today,
            settings.symbols,
            candle_length=settings.candle_length,
            unit=settings.unit,
        )
    else:
        raise ValueError(f"Unsupported data_source: {settings.data_source}")

    strategy = StaticBounce(
        logger,
        aggregator.get_candles(),
        proximity_threshold=0.00, # Unused when simply discovering signal data
        reward_points=0.00, # Unused when simply discovering signal data
        risk_points=0.00, # Unused when simply discovering signal data
        price_tolerance=settings.price_tolerance,
        min_separation=settings.min_separation,
        top_n=settings.top_n,
    )

    strategy.print_static_levels()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tunable support and resistance level finder"
    )
    DiscoverSettings.set_args(parser)
    args = parser.parse_args()

    main(args)
