from chart import Chart, Level
from pythonjsonlogger import jsonlogger

import argparse
import config
import logging


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def start(args):
    # Initialize the root logger
    logger = init_logger()

    # Load settings from yaml config
    settings = config.Settings.load_yaml(args.config)

    levels = []
    for level in settings.levels:
        value = level.pop("value")
        levels.append(Level(value, **level))

    chart = Chart(
        logger,
        settings.api_base,
        settings.market_hub_base,
        settings.user,
        settings.api_key,
        settings.account_id,
        settings.contract_id,
        settings.contract_size,
        levels=levels,
    )

    logger.info(
        "level farmer start", extra={"levels": [level.__dict__ for level in levels]}
    )

    # Start concurrent threads and block
    # chart.start_candle_poller()
    chart.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simple, tunable, algorithmic trading bot"
    )
    config.Settings.set_discover_args(parser)
    config.Settings.set_standard_args(parser)
    args = parser.parse_args()

    start(args)
