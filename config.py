from pydantic import BaseModel
from typing import List, Dict, Any

import yaml


class Settings(BaseModel):
    api_base: str
    market_hub_base: str
    user: str
    api_key: str
    account_id: int
    contract_id: str
    contract_size: int
    levels: List[Dict[str, Any]]

    @classmethod
    def load_yaml(cls, path: str = "config.yaml") -> "Settings":
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    @classmethod
    def set_backtest_args(cls, parser):
        parser.add_argument(
            "--backtest-date", type=str, default="20250827", help="The date to backtest"
        )
        parser.add_argument(
            "--historical-context",
            type=int,
            default=10,
            help="The number of days prior to the backtest date from which historical data is collected",
        )
        parser.add_argument(
            "--ticker-type",
            type=str,
            default="csv",
            help="Specifies the source of the ticks being replayed",
        )
        parser.add_argument(
            "--data-dir",
            type=str,
            default="cl_historical",
            help="Specifies the data directory to be used",
        )

    @classmethod
    def set_standard_args(cls, parser):
        parser.add_argument(
            "--config", type=str, default="config.yaml", help="Config file path"
        )

    @classmethod
    def set_discover_args(cls, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=5,
            help="The number of days back (from now) to analyze",
        )
        parser.add_argument(
            "--candle-length", type=int, default=5, help="The candle timeframe"
        )
        parser.add_argument(
            "--unit",
            type=str,
            default="minutes",
            help="The unit used to measure the candle length; only minutes or hours supported",
        )
        parser.add_argument(
            "--price-tolerance",
            type=float,
            default=5.0,
            help="Price range within which levels are considered the same",
        )
        parser.add_argument(
            "--min-separation",
            type=int,
            default=10,
            help="Number of candles before/after to consider a high/low isolated",
        )
        parser.add_argument(
            "--top-n",
            type=int,
            default=10,
            help="Number of support/resistance levels to return",
        )
