import pandas as pd
from math import floor
import logging
import binance_client.constants as cts
from datetime import datetime as dtt
from binance_client.stream import BinanceStreamClient
import json

MAX_TICKERS_TO_TRACK = 10

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class StreamsManager:
    def __init__(self, binance, states: dict, test: bool = False):
        self.binance = binance
        self.states = states
        self.streams = []
        self._test_net = test
        self.trades_stream = None

    def _handle_trade_message(self, msg):
        m = json.loads(msg)
        if "result" in m.keys():
            return
        if "stream" in m.keys() and "data" in m.keys():
            self.states["messages"].append(m["data"])
            return
        self.states["messages"].append(m)

    def _create_streams(self):
        self.streams = []
        # logger.info(f"Pairs in Streams: {self.states["pairs"]}")
        for pair in self.states["pairs"]["pair"]:
            self.streams.append(f"{pair.lower()}@trade")
        self.trades_stream = BinanceStreamClient(
            streams=self.streams,
            on_message=self._handle_trade_message,
            test_net=self._test_net,
        )
        self.trades_stream.start()

    def _unsub_old_streams(self):
        if self.trades_stream is None:
            return
        self.trades_stream.stop()

    def refresh(self):
        self._acquire_targets()
        self._unsub_old_streams()
        self._create_streams()

    def stop(self):
        self.trades_stream.stop()  # i.e. stop

    def _acquire_targets(self, ignore_list=[]):
        def get_max_pair_prices():
            logger.info(
                f"Fetching max prices and volumes for {self.states['pairs']['pair'].values}"
            )
            ignore = []
            for pair in self.states["pairs"]["pair"]:
                self.states["max_prices_vols"][pair] = {}
                max_price = 0
                max_vol = 0
                earliest_data = 20000000
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
                pair_age_hours = dtt.now().timestamp() - earliest_data / 3600
                if earliest_data < 24:
                    logger.info(f"Pair {pair} is younger than 24 hours. Ignoring...")
                    ignore.append(pair)
                else:
                    self.states["max_prices_vols"][pair]["max_price"] = max_price
                    self.states["max_prices_vols"][pair]["max_vol"] = max_vol
            if len(ignore) != 0:
                self._acquire_targets(ignore)

        def get_best_growers():
            logger.info("Getting best market growers...")
            self.states["pairs"] = self.states["pairs"][0:0]
            info = (
                self.binance.market_data.twentyfourhour_ticker_price_change_statistics()
            )
            best_tickers_df = pd.DataFrame(columns=["symbol", "change_pct"])
            for i, ticker in enumerate(info["content"]):
                best_tickers_df.loc[i] = [
                    ticker["symbol"],
                    float(ticker["priceChangePercent"]),
                ]
            best_tickers_df = best_tickers_df[
                best_tickers_df["symbol"].str.endswith("BTC")
            ].sort_values(by="change_pct", ascending=False)

            for i, row in best_tickers_df.iterrows():
                if row["symbol"] in ignore_list:
                    continue
                self.states["pairs"].loc[-1] = [row["symbol"], row["change_pct"]]
                self.states["pairs"].index = self.states["pairs"].index + 1
                if len(self.states["pairs"]) > MAX_TICKERS_TO_TRACK:
                    break

        get_best_growers()
        get_max_pair_prices()
