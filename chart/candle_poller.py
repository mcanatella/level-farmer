from datetime import datetime, timedelta, timezone

import numpy as np
import pandas
import threading
import time as t


class CandlePoller:
    def __init__(
        self, logger, market_data_client, contract_id, refresh_interval=10, periods=3600
    ):
        self.logger = logger
        self.market_data_client = market_data_client
        self.contract_id = contract_id
        self.refresh_interval = refresh_interval
        self.periods = periods

        self.stop_flag = threading.Event()

        self.candles = None
        self.vwap = Vwap()

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.stop_flag.set()

    def run(self):
        while not self.stop_flag.is_set():
            try:
                self.poll()
            except Exception as e:
                self.logger.error(
                    "encountered exception while polling candles",
                    extra={"event": "candle_poll_error", "value": e},
                )
            t.sleep(self.refresh_interval)

    def poll(self):
        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=self.periods)

        self.candles = self.market_data_client.bars(
            contractId=self.contract_id,
            live=False,
            startTime=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            endtime=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            unit=2,
            unitNumber=1,
            limit=self.periods,
            includePartialBar=False,
        )

        if not self.candles:
            self.logger.warning(
                "no bars received while polling candles",
                extra={"event": "candle_poll_warning"},
            )
            return

        self.vwap.refresh(self.candles)

        self.logger.info(
            "successfully polled candles",
            extra={
                "event": "poll_candles",
                "count": len(self.candles),
                "vwap": self.vwap.current()[0],
            },
        )


class Vwap:
    def __init__(self):
        self.df = None

    def refresh(self, candles):
        # Load into dataframe and sort by oldest to newest bar
        self.df = pandas.DataFrame(candles)
        self.df.sort_values("t", inplace=True)
        self.df.reset_index(drop=True, inplace=True)

        # Vwap
        self.df["typical_price"] = (self.df["h"] + self.df["l"] + self.df["c"]) / 3
        self.df["price_volume"] = self.df["typical_price"] * self.df["v"]
        self.df["cumulative_price_volume"] = self.df["price_volume"].cumsum()
        self.df["cumulative_volume"] = self.df["v"].cumsum()
        self.df["vwap"] = (
            self.df["cumulative_price_volume"] / self.df["cumulative_volume"]
        )

        # Standard deviations
        self.df["vwap_diff"] = self.df["typical_price"] - self.df["vwap"]
        self.df["weighted_diff_sq"] = self.df["vwap_diff"] ** 2 * self.df["v"]
        self.df["cumulative_weighted_diff_sq"] = self.df["weighted_diff_sq"].cumsum()
        self.df["variance"] = (
            self.df["cumulative_weighted_diff_sq"] / self.df["cumulative_volume"]
        )
        self.df["std_dev"] = np.sqrt(self.df["variance"])
        self.df["vwap_upper"] = self.df["vwap"] + 2 * self.df["std_dev"]
        self.df["vwap_lower"] = self.df["vwap"] - 2 * self.df["std_dev"]

    def current(self):
        if self.df is None:
            return (None, None, None)

        return (
            round(self.df.iloc[-1]["vwap"], 2),
            round(self.df.iloc[-1]["vwap_upper"], 2),
            round(self.df.iloc[-1]["vwap_lower"], 2),
        )
