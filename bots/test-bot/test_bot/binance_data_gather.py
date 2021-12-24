from binance_client.client import BinanceClient
import binance_client.constants as cts
import pandas as pd
from datetime import datetime as dtt
from math import floor
from os import listdir
import concurrent.futures

symbols = []
binance = BinanceClient(keys_file="/home/lavin/.binance/keys.json")
r = binance.market_data.exchange_information()["content"]
for symbol in r["symbols"]:
    if symbol["symbol"].endswith("BTC"):
        symbols.append(symbol["symbol"])

existing_csvs = listdir("./bnndata/")


def download(symbol):
    minute_data = pd.DataFrame(
        columns=[
            "ts",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "number_of_trades",
        ]
    )
    if symbol + ".csv" in existing_csvs:
        print(f"Already downloaded {symbol}")
        return minute_data, symbol
    code = 200
    end_time = floor(dtt.now().timestamp() * 1000)
    start_time = end_time - (15 * 60 * 1000 * 1000)
    while code == 200:
        print(
            f"Symbol: {symbol} Start: {pd.to_datetime(start_time, unit='ms')} End: {pd.to_datetime(end_time, unit='ms')}"
        )
        r = binance.market_data.kline_candlestick_data(
            symbol=symbol,
            interval=cts.KLINE_INTERVAL_MINUTES_15,
            start_time=start_time,
            end_time=end_time,
            limit=1000,
        )
        code = r["http_code"]
        if code != 200 or len(r["content"]) == 0:
            print(f"CODE: {code} CONTENT: \n{r['content']}")
            break
        for kline in r["content"]:
            row = pd.DataFrame(
                columns=[
                    "ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "quote_volume",
                    "number_of_trades",
                ]
            )
            row["ts"] = [kline[0]]
            row["open"] = [float(kline[1])]
            row["high"] = [float(kline[2])]
            row["low"] = [float(kline[3])]
            row["close"] = [float(kline[4])]
            row["volume"] = [float(kline[5])]
            row["quote_volume"] = [float(kline[7])]
            row["number_of_trades"] = [kline[8]]
            minute_data = minute_data.append(row)
        end_time = start_time
        start_time = end_time - (15 * 60 * 1000 * 1000)
    return minute_data, symbol


executor = concurrent.futures.ProcessPoolExecutor(6)
futures = [executor.submit(download, symbol) for symbol in symbols]
for future in concurrent.futures.as_completed(futures):
    df, csv = future.result()
    if df.empty:
        print("EMPTY!!!!!!!!!!!")
        continue
    print(f"Writing to {csv}.csv")
    df.to_csv(f"./bnndata/{csv}.csv", index=False, header=False)
