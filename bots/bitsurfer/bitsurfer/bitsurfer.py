from binance_client.client import BinanceClient
from binance_client.stream import BinanceStreamClient
import binance_client.constants as cts
from animation import Animator
from crypto_predictors.sgd import SGDPredictor
import pandas as pd
import numpy as np
import threading
from multiprocessing import Process
import time
from datetime import datetime as dtt
from datetime import timedelta
import schedule
import json
from math import floor
import logging

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
        self.predictor = SGDPredictor(
            batch_size_mins=self._ops_frequency,
            train_data_path="../data/",
            future_periods=self._future_periods,
            ops_time_unit=self._ops_time_unit,
        )
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
        self._prediction_cycles = 0

    def handle_trade_message(self, msg):
        m = json.loads(msg)
        if "result" in m.keys():
            return
        if "stream" in m.keys() and "data" in m.keys():
            self._messages.append(m["data"])
            return
        self._messages.append(m)

    def create_streams(self):
        streams = []
        for pair in self._pairs:
            streams.append(f"{pair.lower()}@trade")
        self.trades_stream = BinanceStreamClient(
            streams=streams, on_message=self.handle_trade_message
        )
        self.trades_stream.start()

    def _run_prediction(self):
        for i, m in enumerate(self._messages):
            try:
                ts = int(floor(m["E"] / 1000))
                price = float(m["p"])
                vol = float(m["q"])
                pair = m["s"]
                self._trades_df.loc[i] = [ts, price, vol, pair]
            except KeyError as e:
                logger.error(f"Key error for message {m}")
        for pair in self._pairs:
            pair_df = (
                self._trades_df[self._trades_df["pair"] == pair]
                .drop(columns=["pair"])
                .reset_index(drop=True)
                .astype(float)
            )
            ts_most_recent = max(pair_df["ts"]) - self._ops_frequency * 60 * 2
            most_recent_idx = pair_df[pair_df["ts"] > ts_most_recent].iloc[0].name
            if most_recent_idx == 0:
                logger.info(f"Not enough data gathered to run prediction for {pair}")
                continue
            if (
                max(pair_df["ts"]) - pair_df.iloc[most_recent_idx]["ts"]
            ) < self._ops_frequency * 60 * 2:
                most_recent_idx -= 1
                predict_df = pair_df.iloc[most_recent_idx:]
            else:
                predict_df = pair_df
            logging.info(f"Performing prediction for pair {pair}")
            results = self.predictor.predict(
                df_test=predict_df,
                max_price=self._max_pair_prices_vols[pair]["max_price"],
                max_vol=self._max_pair_prices_vols[pair]["max_vol"],
            )
            results["prediction"] = (
                results[f"prediction_t+{self._future_periods}"].values
                * self._max_pair_prices_vols[pair]["max_price"]
            )
            results["ts"] = (
                results.index
                + timedelta(minutes=self._ops_frequency * self._future_periods)
            ).values.astype(np.int64) // 10 ** 9
            results["pair"] = pair
            self._prediction_results_df = self._prediction_results_df.append(
                results[["ts", "prediction", "pair"]]
            )
            logger.info(f"LATEST PREDICTION RESULTS {pair}: \n{results.tail(3)}")
        self._calculate_prediction_errors()

    def _calculate_prediction_errors(self):
        if self._prediction_results_df.empty:
            return
        beginning = min(self._prediction_results_df["ts"])
        end = max(self._trades_df["ts"])
        predictions = self._prediction_results_df[
            (self._prediction_results_df["ts"] > beginning)
            & (self._prediction_results_df["ts"] < end)
        ]
        actuals = self._trades_df[
            (self._trades_df["ts"] > beginning) & (self._trades_df["ts"] < end)
        ]
        if predictions.empty or actuals.empty:
            logger.info("Can't calculate predictions error due to lack of data.")
            return
        for pair in self._pairs:
            actual_pair_df = actuals[actuals["pair"] == pair][["ts", "price"]].astype(
                float
            )
            predictions_pair_df = predictions[predictions["pair"] == pair][
                ["ts", "prediction"]
            ].astype(float)
            if actual_pair_df.empty or predictions_pair_df.empty:
                logger.info(f"Can't evaluate prediction performance for {pair}")
                self._prediction_errors_df.loc[pair] = [float("nan"), float("nan")]
                continue
            logger.info(f"Calculating prediction error for {pair}")
            rmse, mae = self.predictor.calculate_errors(
                actual_pair_df, predictions_pair_df
            )
            self._prediction_errors_df.loc[pair] = [rmse, mae]
        logger.info(
            f"CURRENT PREDICTION ERRORS:\n{self._prediction_errors_df.head(10)}"
        )

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

    def run(self):
        self._acquire_targets()
        self.create_streams()
        self._create_animator()
        schedule.every(self._ops_frequency).minutes.do(self._run_prediction)
        schedule.every(30).minutes.do(self._acquire_targets)
        schedule.every(self._get_old_periods()).minutes.do(self._drop_old_entries)
        while not self._should_terminate:
            schedule.run_pending()
            time.sleep(1)

    def _create_animator(self):
        self._animator = Animator(
            pred_df=self._prediction_results_df,
            actual_df=self._trades_df,
            animation_interval=self._ops_frequency * 60,
            number_of_plots=len(self._pairs),
            pairs=self._pairs,
            ops_freq=self._ops_frequency,
        )
        p = Process(target=self._animator.run)
        p.join()

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
        logger.info(f"Shutting down BitSurfer (TM)")
        self.trades_stream.stop()
        self._should_terminate = True


if __name__ == "__main__":
    b = Bitsurfer()
    b.start()
    # time.sleep(*60)
    # b.stop()
