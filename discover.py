from chart import LevelPoller
from projectx_client import Auth, MarketData

import argparse
import config


def run(args):
    # Load settings from yaml config
    settings = config.Settings.load_yaml(args.config)

    auth = Auth(
        base_url=settings.api_base, username=settings.user, api_key=settings.api_key
    )

    jwt_token = auth.login()
    market_data_client = MarketData(settings.api_base, jwt_token)

    level_poller = LevelPoller(
        market_data_client,
        settings.contract_id,
        days=args.days,
        candle_length=args.candle_length,
        unit="minutes",
        price_tolerance=args.price_tolerance,
        min_separation=args.min_separation,
        top_n=args.top_n,
    )

    level_poller.poll()
    top_support, top_resistance = level_poller.calculate_levels()

    # Output top support and resistance levels
    print("\nTop Support Levels:")
    for lvl in top_support:
        print(
            f"  Level: {lvl["price"]:.2f} | Hits: {len(lvl["hits"])} | Score: {lvl["score"]:.2f}"
        )

    print("\nTop Resistance Levels:")
    for lvl in top_resistance:
        print(
            f"  Level: {lvl["price"]:.2f} | Hits: {len(lvl["hits"])} | Score: {lvl["score"]:.2f}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tunable support and resistance level finder"
    )
    config.Settings.set_discover_args(parser)
    config.Settings.set_standard_args(parser)
    args = parser.parse_args()

    run(args)
