from chart import LevelPoller, Level, SignalDispatcher
from colorama import Fore, Style, init
from core import Tick, EngineState, run_engine
from datetime import datetime, date, timedelta
from pathlib import Path
from tickers import CsvTicker
from typing import Any, Iterable, Optional, Dict, List
from zoneinfo import ZoneInfo

import argparse
import asyncio
import config
import json
import logging
import re

FNAME_PREFIX = "glbx-mdp3-"
FNAME_POSTFIX = ".trades.csv"
FNAME_RE = re.compile(rf"{re.escape(FNAME_PREFIX)}(\d{{8}}){re.escape(FNAME_POSTFIX)}$")


def init_logger():
    init(autoreset=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()

    # Set datefmt to only show down to seconds
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def parse_yyyymmdd(s: str) -> date:
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def floor_5min(dt: datetime) -> datetime:
    m = dt.minute - (dt.minute % 5)
    return dt.replace(minute=m, second=0, microsecond=0)


async def build_5m_candles(
    data_dir: str | Path,
    start_date: date,
    end_date: date,
    start_symbol: str,
    end_symbol: str,
) -> List[Dict]:
    data_dir = Path(data_dir)

    # OHLCV state accumulator keyed by (bucket_ts, symbol)
    buckets: Dict[tuple[datetime, str], Dict[str, float]] = {}

    async def handler(tick: Tick, state: Any):
        bkt = floor_5min(tick.t), tick.symbol
        rec = buckets.get(bkt)
        if rec is None:
            # open=first price, high/low init to price, close updates, volume sums
            state[bkt] = {
                "o": tick.price,
                "h": tick.price,
                "l": tick.price,
                "c": tick.price,
                "v": tick.size,
            }
        else:
            if tick.price > rec["h"]:
                rec["h"] = tick.price
            if tick.price < rec["l"]:
                rec["l"] = tick.price
            rec["c"] = tick.price
            rec["v"] += tick.size

    # Collect matching files by filename date
    files: List[Path] = []
    for p in sorted(data_dir.glob("glbx-mdp3-*.trades.csv")):
        m = FNAME_RE.search(p.name)
        if not m:
            continue
        d = parse_yyyymmdd(m.group(1))
        if start_date <= d <= end_date:
            files.append(p)

    for fp in files:
        ticker = CsvTicker(fp, start_symbol, end_symbol)
        await run_engine(ticker, buckets, handler)

    # Flatten to list of dicts, sorted by time then symbol
    out: List[Dict] = []
    for (bkt_ts, sym), rec in sorted(buckets.items(), key=lambda x: (x[0][0], x[0][1])):
        out.append(
            {
                "t": bkt_ts.isoformat().replace("+00:00", "Z"),
                "symbol": sym,
                "o": round(rec["o"], 3),
                "h": round(rec["h"], 3),
                "l": round(rec["l"], 3),
                "c": round(rec["c"], 3),
                "v": int(rec["v"]),
            }
        )
    return out


async def main(args):
    logger = init_logger()

    mock_poller = LevelPoller(
        None,
        "CON.F.US.CLE.U25",
        days=10,
        candle_length=5,
        unit="minutes",
        price_tolerance=0.05,
        min_separation=10,
        top_n=5,
    )

    def handler(tick: Tick, state: Any):
        if state.position is None:
            state.position = mock_dispatcher.check(tick.price, tick.t)
            if state.position is None:
                return

        market_price = state.position["entry"]
        profit_loss = 0
        if state.position["direction"] == "LONG":
            if tick.price >= state.position["take_profit"]:
                profit_loss = round(
                    (state.position["take_profit"] - market_price) * 1000, 2
                )
            elif tick.price <= state.position["stop_loss"]:
                profit_loss = round(
                    (state.position["stop_loss"] - market_price) * 1000, 2
                )
            else:
                return
        else:
            if tick.price <= state.position["take_profit"]:
                profit_loss = round(
                    (market_price - state.position["take_profit"]) * 1000, 2
                )
            elif tick.price >= state.position["stop_loss"]:
                profit_loss = round(
                    (market_price - state.position["take_profit"]) * 1000, 2
                )
            else:
                return

        color = Fore.GREEN if profit_loss > 0 else Fore.RED
        ts_start = (
            state.position["timestamp"]
            .replace(microsecond=0)
            .astimezone(ZoneInfo("America/Chicago"))
        )
        ts_end = tick.t.replace(microsecond=0).astimezone(ZoneInfo("America/Chicago"))
        logger.info(
            f"{color}Trade completed, Start = {ts_start}, End = {ts_end}, PnL = ${profit_loss:.2f}{Style.RESET_ALL}"
        )

        # Reset position
        state.position = None

    # Parse string version of the back test date into a date object
    d = datetime.strptime(args.backtest_date, "%Y%m%d").date()

    # Subtract n days and 1 day to get the candlestick timeframe
    start_date = d - timedelta(days=args.historical_context)
    end_date = d - timedelta(days=1)

    # TODO: define a protocol with a query method that contain things like calls to build_5m_candles (from csv) or
    # actual api queries for historical data depending on the specific implementation of the protocol.
    mock_poller.candles = await build_5m_candles(
        "cl_historical", start_date, end_date, "CLU5", "CLV5"
    )

    # Once the mock poller has candles populated, it can calculate support and resistance levels
    support_dict, resistance_dict = mock_poller.calculate_levels()

    support = [
        Level(
            round(lvl["price"], 2),
            name=None,
            support=True,
            resistance=True,
            proximity_threshold=0.03,
            reward_points=0.10,
            risk_points=0.15,
        )
        for lvl in support_dict
    ]
    resistance = [
        Level(
            round(lvl["price"], 2),
            name=None,
            support=True,
            resistance=True,
            proximity_threshold=0.03,
            reward_points=0.10,
            risk_points=0.15,
        )
        for lvl in resistance_dict
    ]

    # The mock signal dispatcher will be used as we traverse tick data for a particular trading day
    mock_dispatcher = SignalDispatcher(logger, levels=(support + resistance))

    state = EngineState()
    filename = f"{args.data_dir}/glbx-mdp3-{args.backtest_date}.trades.csv"
    ticker = CsvTicker(filename, "CLV5", "CLV5")
    await run_engine(ticker, state, handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tunable support and resistance level finder"
    )
    config.Settings.set_backtest_args(parser)
    args = parser.parse_args()

    asyncio.run(main(args))
