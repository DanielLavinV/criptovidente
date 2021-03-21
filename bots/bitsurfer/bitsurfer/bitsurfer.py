from binance_client.client import BinanceClient
from binance_client.stream import BinanceStreamClient
import binance_client.constants as cts
import pandas as pd
import threading
import time
from datetime import datetime as dtt
import schedule
import json
from math import floor
from predictions import PredictionsManager
from wallet import WalletManager
import logging

pd.set_option("display.float_format", "{:.10f}".format)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] -%(levelname)s- | %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)


class Bitsurfer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.binance = BinanceClient("/home/lavin/.binance/keys.json", False)
        self.binance_test = BinanceClient("/home/lavin/.binance/keys.json", True)
        self._ops_frequency = 1
        self._ops_time_unit = "T"
        self._future_periods = 1
        self._prediction_results_df = pd.DataFrame(
            columns=[
                "ts",
                "prediction",
                "pair",
            ]  # "ts" references when the prediction WILL happen
        )
        self._trades_df = pd.DataFrame(columns=["ts", "price", "vol", "pair"])
        self._prediction_errors_df = pd.DataFrame(columns=["rmse", "mae"])
        self._pairs = []
        self._messages = []
        self._max_pair_prices_vols = {}
        self._should_terminate = False
        self.predictions_manager = PredictionsManager(
            messages=self._messages,
            pairs=self._pairs,
            ops_freq=self._ops_frequency,
            trades_df=self._trades_df,
            pred_results_df=self._prediction_results_df,
            pred_errors_df=self._prediction_errors_df,
            future_periods=self._future_periods,
            max_prices_vols=self._max_pair_prices_vols,
            ops_time_unit=self._ops_time_unit,
        )
        self.wallet_manager = WalletManager(client=self.binance)

    def handle_trade_message(self, msg):
        m = json.loads(msg)
        if "result" in m.keys():
            return
        if "stream" in m.keys() and "data" in m.keys():
            self._messages.append(m["data"])
            return
        self._messages.append(m)

    def _create_streams(self):
        streams = []
        for pair in self._pairs:
            streams.append(f"{pair.lower()}@trade")
        self.trades_stream = BinanceStreamClient(
            streams=streams, on_message=self.handle_trade_message
        )
        self.trades_stream.start()

    def _drop_old_entries(self):
        logger.info("Cleaning up old entries from dataframes...")
        self._trades_df = self._trades_df[-5000:].reset_index(drop=True)
        self._prediction_results_df = self._prediction_results_df[-5000:].reset_index(
            drop=True
        )
        self._prediction_errors_df = self._prediction_errors_df.dropna()
        self._messages = self._messages[-5000:]

    def _get_old_periods(self):
        return self._ops_frequency * 10

    def init(self):
        self._acquire_targets()
        self._create_streams()

    def run(self):
        self.init()
        schedule.every(self._ops_frequency).minutes.do(
            self.predictions_manager.run_prediction
        )
        schedule.every(30).minutes.do(self._acquire_targets)
        schedule.every(self._get_old_periods()).minutes.do(self._drop_old_entries)
        while not self._should_terminate:
            schedule.run_pending()
            time.sleep(1)

    def _acquire_targets(self, ignore_list=[]):
        def get_max_pair_prices():
            logger.info(f"Fetching max prices and volumes for {self._pairs}")
            ignore = []
            for pair in self._pairs:
                self._max_pair_prices_vols[pair] = {}
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
                    self._max_pair_prices_vols[pair]["max_price"] = max_price
                    self._max_pair_prices_vols[pair]["max_vol"] = max_vol
            if len(ignore) != 0:
                self._pairs = []
                self._acquire_targets(ignore)

        def get_best_growers():
            logger.info("Getting best market growers...")
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
                best_tickers_df["symbol"].str.contains("BTC")
            ].sort_values(by="change_pct", ascending=False)
            logger.info(f"Best tickers:\n {best_tickers_df.head()}")

            for i, row in best_tickers_df.iterrows():
                if row["symbol"] in ignore_list:
                    continue
                self._pairs.append(row["symbol"])
                if len(self._pairs) > 2:
                    break

        get_best_growers()
        get_max_pair_prices()

    def stop(self):
        logger.info("Shutting down BitSurfer (TM)")
        self.trades_stream.stop()
        self._should_terminate = True


if __name__ == "__main__":
    b = Bitsurfer()
    b.start()
