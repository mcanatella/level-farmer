from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def calculate_static_levels(
    candles, min_separation, top_n, tick_tolerance, tick_size, decay_half_life_days
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    # Convert the raw candle data from a list of dicts into a DataFrame
    df = pd.DataFrame(candles)
    df["t"] = pd.to_datetime(df["t"])
    df.set_index("t", inplace=True)

    support_candidates = []
    resistance_candidates = []
    for i in range(min_separation, len(df) - min_separation):
        row = df.iloc[i]
        ts = df.index[i]
        low = row["l"]
        high = row["h"]
        volume = row["v"]

        # Check for isolated low; this low must be lower than lows of surrounding candles
        is_isolated_low = all(
            low < df.iloc[i - j]["l"] and low < df.iloc[i + j]["l"]
            for j in range(1, min_separation + 1)
        )

        if is_isolated_low:
            support_candidates.append((low, volume, ts))

        # Check for isolated high; this high must be higher than highs of surrounding candles
        is_isolated_high = all(
            high > df.iloc[i - j]["h"] and high > df.iloc[i + j]["h"]
            for j in range(1, min_separation + 1)
        )

        if is_isolated_high:
            resistance_candidates.append((high, volume, ts))

    # Return top support and resistance levels as a list of dicts
    support_dicts = _cluster_levels(
        support_candidates, tick_tolerance, tick_size, decay_half_life_days
    )[:top_n]
    resistance_dicts = _cluster_levels(
        resistance_candidates, tick_tolerance, tick_size, decay_half_life_days
    )[:top_n]

    return support_dicts, resistance_dicts


def _cluster_levels(
    candidates, tick_tolerance, tick_size, decay_half_life_days
) -> List[Dict[str, Any]]:
    if not candidates:
        return []

    # For recency weighting
    now = max(ts for _, _, ts in candidates)
    half_life = pd.Timedelta(days=decay_half_life_days)
    lam = np.log(2) / half_life.total_seconds()

    clusters: List[Dict[str, Any]] = []

    # Sort by price
    for price, volume, ts in sorted(candidates, key=lambda x: x[0]):
        found_cluster = False

        for cluster in clusters:
            if abs(price - cluster["price"]) <= tick_tolerance * tick_size:
                cluster["hits"].append(price)
                cluster["volumes"].append(volume)
                cluster["timestamps"].append(ts)
                found_cluster = True
                break

        if not found_cluster:
            clusters.append(
                {
                    "price": price,
                    "hits": [price],
                    "volumes": [volume],
                    "timestamps": [ts],
                }
            )

    for cluster in clusters:
        hit_count = len(cluster["hits"])
        avg_volume = float(np.mean(cluster["volumes"]))

        # recency weights for this cluster
        ages = np.array([(now - ts).total_seconds() for ts in cluster["timestamps"]])
        recency_weights = np.exp(-lam * ages)

        # effective recency factor = average weight in [0, 1]
        recency_factor = float(np.mean(recency_weights))

        # You can tune this; squaring hit_count gives more love to multi-hit levels
        cluster["score"] = (hit_count**2) * avg_volume * recency_factor

        cluster["price"] = float(np.mean(cluster["hits"]))

    return sorted(clusters, key=lambda x: x["score"], reverse=True)
