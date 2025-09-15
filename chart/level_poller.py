from datetime import datetime, timedelta, timezone

import math
import numpy as np
import pandas as pd


class LevelPoller:
    def __init__(
        self,
        market_data_client,
        contract_id,
        days=5,
        candle_length=5,
        unit="minutes",
        price_tolerance=5.0,
        min_separation=10,
        top_n=5,
    ):
        self.market_data_client = market_data_client
        self.contract_id = contract_id
        self.unit = 3 if unit == "hours" else 2
        self.days = days
        self.candle_length = candle_length
        self.price_tolerance = price_tolerance
        self.min_separation = min_separation
        self.top_n = top_n

        self.support_candidates = []
        self.resistance_candidates = []

        self.candles = None

    def calculate_levels(self):
        # Convert the raw candle data (list of dicts) into a DataFrame
        df = pd.DataFrame(self.candles)
        df["t"] = pd.to_datetime(df["t"])
        df.set_index("t", inplace=True)

        for i in range(self.min_separation, len(df) - self.min_separation):
            row = df.iloc[i]
            low = row["l"]
            high = row["h"]
            volume = row["v"]

            # Check for isolated low; this low must be lower than lows of surrounding candles
            is_isolated_low = all(
                low < df.iloc[i - j]["l"] and low < df.iloc[i + j]["l"]
                for j in range(1, self.min_separation + 1)
            )

            if is_isolated_low:
                self.support_candidates.append((low, volume))

            # Check for isolated high; this high must be higher than highs of surrounding candles
            is_isolated_high = all(
                high > df.iloc[i - j]["h"] and high > df.iloc[i + j]["h"]
                for j in range(1, self.min_separation + 1)
            )

            if is_isolated_high:
                self.resistance_candidates.append((high, volume))

        # Return top support and resistance levels
        top_support = self._cluster_levels(
            self.support_candidates, self.price_tolerance
        )[: self.top_n]
        top_resistance = self._cluster_levels(
            self.resistance_candidates, self.price_tolerance
        )[: self.top_n]

        return top_support, top_resistance

    def poll(self):
        num_candles = math.ceil(60 / self.candle_length) * 24 * self.days
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=self.days)

        # Poll candles from server
        self.candles = self.market_data_client.bars(
            contractId=self.contract_id,
            live=False,
            startTime=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            endtime=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            unit=self.unit,
            unitNumber=self.candle_length,
            limit=num_candles,
            includePartialBar=False,
        )

    def _cluster_levels(self, candidates, tolerance):
        """
        Helper method to group price levels within `tolerance` and score them based on
        - number of hits (confirmations)
        - average volume during those hits
        """
        clusters = []

        for price, volume in sorted(candidates):
            found_cluster = False

            # Try to match this level to an existing cluster
            for cluster in clusters:
                if abs(price - cluster["price"]) <= tolerance:
                    cluster["hits"].append(price)
                    cluster["volumes"].append(volume)
                    found_cluster = True
                    break

            # If no matching cluster, start a new one
            if not found_cluster:
                clusters.append(
                    {
                        "price": price,
                        "hits": [price],
                        "volumes": [volume],
                    }
                )

        # Calculate a score for each cluster
        for cluster in clusters:
            hit_count = len(cluster["hits"])
            avg_volume = np.mean(cluster["volumes"])
            cluster["score"] = hit_count * avg_volume
            # Average the cluster's price level
            cluster["price"] = np.mean(cluster["hits"])

        # Sort clusters by score, highest first
        return sorted(clusters, key=lambda x: x["score"], reverse=True)
