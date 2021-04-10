import pandas as pd
from math import floor
import logging
import binance_client.constants as cts
from datetime import datetime as dtt
from binance_client.stream import BinanceStreamClient
import json
from typing import List

MAX_TICKERS_TO_TRACK = 10
WORKING_QUOTE_ASSET = "BTC"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class StreamsManager:
    def __init__(self, binance, states: dict):
        self.binance = binance
        self.states = states
        self.streams = []
        self.trades_stream = None

    def _handle_trade_message(self, msg):
        m = json.loads(msg)
        if "result" in m.keys():
            return
        if "stream" in m.keys() and "data" in m.keys():
            self.states["messages"].append(m["data"])
            return
        self.states["messages"].append(m)

    def create_streams(self):
        self.streams = []
        # logger.info(f"Pairs in Streams: {self.states["pairs"]}")
        for pair in self.states["pairs"]["pair"]:
            self.streams.append(f"{pair.lower()}@trade")
        self.trades_stream = BinanceStreamClient(
            streams=self.streams, on_message=self._handle_trade_message
        )
        self.trades_stream.start()

    def refresh(self):
        self.acquire_targets()
        self._unsub_old_streams()
        self.create_streams()

    def _unsub_old_streams(self):
        if self.trades_stream is None:
            return
        self.trades_stream.stop()

    def stop(self):
        self.trades_stream.stop()  # i.e. stop

    def get_max_pair_prices(self, targets: List[str]) -> List[str]:
        logger.info(f"Fetching max prices and volumes for {targets}")
        ignore = []
        for pair in targets:
            self.states["max_prices_vols"][pair] = {}
            max_price = 0
            max_vol = 0
            earliest_data = 2000000000
            data = self.binance.market_data.kline_candlestick_data(
                symbol=pair,
                interval=cts.KLINE_INTERVAL_MONTHS_1,
                start_time=floor(dtt.timestamp(dtt(2010, 1, 1))) * 1000,
                end_time=floor(dtt.timestamp(dtt.now())) * 1000,
                limit=500,
            )["content"]
            for kline in data:
                if floor(kline[0] / 1000) < earliest_data:
                    earliest_data = floor(kline[0] / 1000)
                if float(kline[2]) > max_price:
                    max_price = float(kline[2])
                if float(kline[5]) > max_vol:
                    max_vol = float(kline[5])
            pair_age_hours = (dtt.now().timestamp() - earliest_data) / 3600
            if pair_age_hours < 24:
                logger.info(f"Pair {pair} is younger than 24 hours. Ignoring...")
                ignore.append(pair)
            else:
                self.states["max_prices_vols"][pair]["max_price"] = max_price
                self.states["max_prices_vols"][pair]["max_vol"] = max_vol
        return [pair for pair in targets if pair not in ignore]

    def get_best_growers(self) -> pd.DataFrame:
        logger.info("Getting best market growers...")
        best_tickers_df = pd.DataFrame(columns=["symbol", "change_pct"])
        info = self.binance.market_data.twentyfourhour_ticker_price_change_statistics()
        for i, ticker in enumerate(info["content"]):
            best_tickers_df.loc[i] = [
                ticker["symbol"],
                float(ticker["priceChangePercent"]),
            ]
        best_tickers_df = best_tickers_df[
            best_tickers_df["symbol"].str.endswith("BTC")
        ].sort_values(by="change_pct", ascending=False)

        return best_tickers_df

    def compare_growers_and_balances(self, best_growers_df: pd.DataFrame) -> List[str]:
        best_growers = [
            bg for bg in best_growers_df[:MAX_TICKERS_TO_TRACK]["symbol"].values
        ]
        symbols_in_holdings = []
        for asset, balance in self.states["balances"].items():
            if asset == "BTC" or asset == "USDT":
                continue
            symbol = asset + WORKING_QUOTE_ASSET
            min_lot_size = self.states["trade_rules"][symbol][cts.FILTER_TYPE_LOT_SIZE][
                "minQty"
            ]
            if balance > min_lot_size:
                symbols_in_holdings.append(symbol)
        extras = [
            symbol for symbol in symbols_in_holdings if symbol not in best_growers
        ]
        best_growers.extend(extras)
        return best_growers

    def acquire_targets(self):
        bg = self.get_best_growers()
        targets = self.compare_growers_and_balances(bg)
        refined_targets = self.get_max_pair_prices(targets)
        pairs_df = bg[bg["symbol"].isin(refined_targets)]
        pairs_df.columns = ["pair", "growth"]
        self.states["pairs"] = pairs_df
