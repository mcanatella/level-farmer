import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from tabulate import tabulate

from calculations import calculate_static_levels
from core import Tick


class StaticBounce:
    def __init__(
        self,
        logger: logging.Logger,
        candles: List[Dict[str, Any]],
        tick_size: float,
        proximity_threshold: int,
        reward_ticks: int,
        risk_ticks: int,
        tick_tolerance: int,
        min_separation: int,
        top_n: int,
        decay_half_life_days: float,
    ) -> None:
        # Logs trade signals
        self.logger = logger

        # Contains data for historical analysis
        self.candles = candles

        # Tick size for the instrument being traded
        self.tick_size = tick_size

        # Bounce parameters
        self.proximity_threshold = proximity_threshold
        self.reward_ticks = reward_ticks
        self.risk_ticks = risk_ticks

        # Static level calculation parameters applied to historical candles
        self.tick_tolerance = tick_tolerance
        self.min_separation = min_separation
        self.top_n = top_n
        self.decay_half_life_days = decay_half_life_days

        # Static levels
        self.support: List[Dict[str, Any]] = []
        self.resistance: List[Dict[str, Any]] = []

        # self.calculate_static_levels()
        self.support, self.resistance = calculate_static_levels(
            self.candles,
            self.min_separation,
            self.top_n,
            self.tick_tolerance,
            self.tick_size,
            self.decay_half_life_days,
        )

        # Convert support and resistance to a single dictionary for fast lookups by value when
        # checking for signals.
        # Support and resistan
        # Because this is a demo strategy, we will treat support and resistance the same.
        self.levels = {}
        for lvl in self.support + self.resistance:
            # self.levels[lvl.value] = lvl
            # Round level price to 2 decimal places for consistency
            lvl["price"] = round(lvl["price"], 2)  # TODO: make precision configurable

            # This particular strategy implementation treats all levels as both support and resistance
            lvl["support"] = True
            lvl["resistance"] = True
            self.levels[lvl["price"]] = lvl

        # {'price': 60.615, 'hits': [np.float64(60.59), np.float64(60.64)], 'volumes': [np.float64(1028.0), np.float64(1779.0)], 'timestamps': [Timestamp('2026-01-22 08:30:00+0000', tz='UTC'), Timestamp('2026-01-21 16:00:00+0000', tz='UTC')], 'score': 4143.313950708893}, 61.86: {'price': 61.86, 'hits': [np.float64(61.86)], 'volumes': [np.float64(4040.0)], 'timestamps': [Timestamp('2026-01-27 13:50:00+0000', tz='UTC')], 'score': 3855.7036815599336}

        # Last level traded to avoid retests
        self.last_level_traded: float | None = None

    def check(self, tick: Tick, timestamp: Any = None) -> Dict[str, Any] | None:
        if not self.levels:
            return None

        # Check if the current price is in proximity to any of our levels and signal accordingly
        signals = []
        for level_key in self.levels:
            level = self.levels[level_key]
            distance = abs(tick.price - level["price"])

            # If the current price is close enough to the level, then we may need to emit a LONG or
            # SHORT signal.
            if distance <= (self.proximity_threshold * self.tick_size):
                # Emit a SHORT signal if the current price is slightly under a resistance level
                if tick.price < level["price"] and level["resistance"]:
                    signals.append((level_key, level, distance, "SHORT"))
                # Emit a LONG signal if the current price is slightly over a support level
                elif tick.price > level["price"] and level["support"]:
                    signals.append((level_key, level, distance, "LONG"))

        # If signals is empty, then there is nothing to act on for now
        if not signals:
            return None

        # Pick the closest qualifying level
        level_key, level, _, direction = min(signals, key=lambda x: x[2])

        # Abort if this is a retest of the level
        if self.last_level_traded == level_key:
            return None

        entry = tick.price

        take_profit = (
            entry + self.reward_ticks * self.tick_size
            if direction == "LONG"
            else entry - self.reward_ticks * self.tick_size
        )
        take_profit = round(take_profit, 2)

        stop_loss = (
            entry - self.risk_ticks * self.tick_size
            if direction == "LONG"
            else entry + self.risk_ticks * self.tick_size
        )
        stop_loss = round(stop_loss, 2)

        self.logger.info(
            f"{direction} signal from {level_key} at {entry}",
            extra={
                "timestamp": timestamp,
                "event": "signal_detected",
                "direction": direction,
                "entry": entry,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "trigger_level": level_key,
            },
        )

        self.last_level_traded = level_key

        return {
            "timestamp": timestamp,
            "direction": direction,
            "entry": entry,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "level": level_key,
        }

    def reset(self) -> None:
        self.last_level_traded = None

    def __repr__(self) -> str:
        headers = ["Level", "Hits", "Score"]

        support_table = tabulate(
            [
                (f"{lvl['price']:.2f}", len(lvl["hits"]), f"{lvl['score']:.2f}")
                for lvl in self.support
            ],
            headers,
            tablefmt="pretty",
        )

        resistance_table = tabulate(
            [
                (f"{lvl['price']:.2f}", len(lvl["hits"]), f"{lvl['score']:.2f}")
                for lvl in self.resistance
            ],
            headers,
            tablefmt="pretty",
        )

        return (
            "\nTop Support Levels:\n"
            + support_table
            + "\n\nTop Resistance Levels:\n"
            + resistance_table
        )
