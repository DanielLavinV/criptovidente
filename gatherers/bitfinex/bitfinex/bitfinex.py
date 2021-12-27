from bitfinex_client.rest_client import BitfinexRestClient
from bitfinex_client import constants
from datetime import datetime as dtt, timedelta
import pandas as pd
from time import sleep
import os

client = BitfinexRestClient('caca', 'caca')

start_time = dtt.now()
candles_per_call = 5000
timeframe = 15  # minutes
timeframe_str = constants.TIMEFRAME_15m
backwards_delta = timedelta(minutes=timeframe * candles_per_call)
all_symbols = client.public.configs(param_string='list:pair:exchange')['content'][0]

for s in all_symbols:
    period_end = start_time
    period_start = start_time - backwards_delta
    s = 't' + s  # trading
    if os.path.exists(f"data/{s.replace(':','')}.csv"):
        print(f"Skipping {s}")
        continue
    symbols_df = pd.DataFrame(columns=['mts', 'open', 'close', 'high', 'low', 'volume'])
    while True:
        candles = client.public.candles(
            symbol=s,
            timeframe=timeframe_str,
            end=period_end.timestamp() * 1000,
            start=period_start.timestamp() * 1000,
            limit=candles_per_call,
            section='hist'
        )['content']
        if not candles:
            break
        print(f"Received {len(candles)} candles.")
        for c in candles:
            symbols_df = symbols_df.append(c, ignore_index=True)
        period_end = period_start
        period_start = period_start - backwards_delta
        sleep(0.5)
    with open(f"data/{s.replace(':','')}.csv", 'w+') as f:
        symbols_df.to_csv(f, sep=';', index=False,)
        f.close()
