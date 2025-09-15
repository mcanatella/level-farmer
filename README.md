## To Do
- Finish adding type annotations and setup type checker
- Extend support to multiple API schemas (only [ProjectX](https://gateway.docs.projectx.com/docs/intro) currently supported)
- Update SignalR websocket feed to implement the Ticker protocol (skeleton below)
- Implement `--auto` feature which will allow the bot to auto discover the levels it watches on startup
- Convert `backtest.py` to use an actual test framework
- Setup CI pipeline which, at a minimum, runs the type checker and linter

## Config Example

```yaml
# API base for querying candles and managing orders
api_base: "https://api.topstepx.com"

# API base for realtime market data feed
market_hub_base: "https://rtc.topstepx.com/hubs/market"

# Account info
user: "myuser"
api_key: "abc123"
account_id: 123456789

# Contract ID used by the bot and discovery tool
contract_id: "CON.F.US.CLE.V25"

# Number of contracts per trade the bot / backtest tool will buy / sell when signaled
contract_size: 1

# Manually configured levels that the bot (farm.py) will watch on startup
levels:
  - value: 61.77
    support: true
    resistance: true
    proximity_threshold: .02
    reward_points: .10
    risk_points: .15
  - value: 62.41
    support: true
    resistance: true
    proximity_threshold: .02
    reward_points: .10
    risk_points: .15
  - value: 62.73
    support: true
    resistance: true
    proximity_threshold: .02
    reward_points: .10
    risk_points: .15
```

## Usage Examples

### The Discovery Tool

The discovery tool can be used to identify static price levels to predict reversals. In the following example I query the top 5 support and resistance levels using 5 minute candles over the past 10 days. For confirmations beyond the first, the spike or valley must have occurred within + or - the `price-tolerance`. In this example, the `price-tolerance` was $0.05.

```bash
(venv) example@rd01:~/Code/level-farmer$ python discover.py \
  --days 10 \
  --top-n 5 \
  --min-separation 10 \
  --candle-length 5 \
  --price-tolerance .05 \
  --config config.cl.yaml

Top Support Levels:
  Level: 63.62 | Hits: 2 | Score: 6563.00
  Level: 62.26 | Hits: 2 | Score: 6003.00
  Level: 63.17 | Hits: 2 | Score: 3219.00
  Level: 62.95 | Hits: 4 | Score: 2796.00
  Level: 61.94 | Hits: 2 | Score: 2753.00

Top Resistance Levels:
  Level: 63.51 | Hits: 3 | Score: 10593.00
  Level: 63.98 | Hits: 1 | Score: 8438.00
  Level: 62.73 | Hits: 3 | Score: 7747.00
  Level: 63.65 | Hits: 3 | Score: 5662.00
  Level: 62.65 | Hits: 3 | Score: 2999.00
```

### The Backtest Tool (work in progress)

Currently, you can run a backtest for a specific day provided you have csv tick data stored in your `data-dir` that conforms to the CME Market Data Platform 3.0 standard. Many test parameters still need to be tuned in code which is why this is marked as a work in progress.

```bash
(venv) example@rd01:~/Code/level-farmer$ python backtest.py --backtest-date 20250904 --data-dir cl_historical
2025-09-15 10:00:32 INFO SHORT signal from 63.8 at 63.79
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-03 19:00:00-05:00, End = 2025-09-03 19:06:56-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.27 at 63.3
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 01:31:49-05:00, End = 2025-09-04 02:02:28-05:00, PnL = $-150.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.15
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 02:02:28-05:00, End = 2025-09-04 02:13:17-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 02:13:17-05:00, End = 2025-09-04 02:53:01-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.15
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 02:53:01-05:00, End = 2025-09-04 03:10:24-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 03:10:56-05:00, End = 2025-09-04 03:19:38-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.16
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 04:18:09-05:00, End = 2025-09-04 04:25:02-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 04:25:07-05:00, End = 2025-09-04 05:16:43-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.15
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 05:16:43-05:00, End = 2025-09-04 05:35:11-05:00, PnL = $-150.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 06:23:03-05:00, End = 2025-09-04 06:33:16-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.16
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 07:50:25-05:00, End = 2025-09-04 07:58:03-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.26
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 07:58:03-05:00, End = 2025-09-04 08:00:44-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.16
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 08:00:44-05:00, End = 2025-09-04 08:09:41-05:00, PnL = $-150.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 08:34:12-05:00, End = 2025-09-04 08:34:56-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.15
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 08:34:56-05:00, End = 2025-09-04 08:37:06-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 08:37:06-05:00, End = 2025-09-04 08:55:55-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.16
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 08:55:55-05:00, End = 2025-09-04 09:03:44-05:00, PnL = $-150.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 09:06:42-05:00, End = 2025-09-04 09:06:44-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.15
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 09:06:44-05:00, End = 2025-09-04 09:07:28-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 09:07:31-05:00, End = 2025-09-04 09:09:59-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO LONG signal from 63.14 at 63.15
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 09:09:59-05:00, End = 2025-09-04 09:23:05-05:00, PnL = $100.00
2025-09-15 10:00:32 INFO SHORT signal from 63.27 at 63.25
2025-09-15 10:00:32 INFO Trade completed, Start = 2025-09-04 09:23:05-05:00, End = 2025-09-04 09:27:36-05:00, PnL = $100.00
```

### The Bot

Starting the bot is straightforward. Once started, it will watch price action and make trades at the configured levels. For now the discovery tool has to be used to identify and manually configured levels, but an `automatic` flag is in the works.

```bash
(venv) example@rd01:~/Code/level-farmer$ python farm.py --config config.cl.yaml
{"asctime": "2025-09-14 21:16:41,963", "levelname": "INFO", "name": "root", "message": "level farmer start", "levels": [{"value": 63.98, "name": null, "support": true, "resistance": true, "proximity_threshold": 0.02, "reward_points": 0.1, "risk_points": 0.15}, {"value": 63.51, "name": null, "support": true, "resistance": true, "proximity_threshold": 0.02, "reward_points": 0.1, "risk_points": 0.15}, {"value": 62.26, "name": null, "support": true, "resistance": true, "proximity_threshold": 0.02, "reward_points": 0.1, "risk_points": 0.15}, {"value": 61.78, "name": null, "support": true, "resistance": true, "proximity_threshold": 0.02, "reward_points": 0.1, "risk_points": 0.15}]}
{"asctime": "2025-09-14 21:16:42,476", "levelname": "INFO", "name": "root", "message": "user opened connection to market hub", "event": "market_hub_connect"}
{"asctime": "2025-09-14 21:16:42,476", "levelname": "INFO", "name": "root", "message": "subscribed to contract CON.F.US.CLE.V25", "event": "market_hub_subscribe"}
```

## SignalRTicker Implementation of Ticker Protocol (Skeleton)

```python
class SignalRTicker:
    def __init__(self, url: str, symbol: str):
        self.url = url
        self.symbol = symbol
        # self._client = YourSignalRClient(url, ...)
        # self._queue: asyncio.Queue[Tick] = asyncio.Queue()

    async def __aiter__(self) -> AsyncIterator[Tick]:
        # Example structure:
        # await self._client.connect()
        # await self._client.subscribe(self.symbol)
        #
        # async def on_message(msg):
        #     tick = Tick(t=..., price=..., size=..., side=..., symbol=self.symbol)
        #     await self._queue.put(tick)
        #
        # while True:
        #     tick = await self._queue.get()
        #     yield tick
        raise NotImplementedError("Wire up your SignalR client here")
```
