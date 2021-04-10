from crypto_predictors.sgd import SGDPredictor
import logging
from datetime import timedelta
from datetime import datetime as dtt
from math import floor
import numpy as np
import binance_client.constants as cts
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PredictionsManager:
    def __init__(self, binance, ops_freq, future_periods, ops_time_unit, states):
        self.binance = binance
        self._ops_frequency = ops_freq
        self._future_periods = future_periods
        self._ops_time_unit = ops_time_unit
        self.states = states
        self.predictor = SGDPredictor(
            batch_size_mins=self._ops_frequency,
            train_data_path="../data/",
            future_periods=self._future_periods,
            ops_time_unit=self._ops_time_unit,
        )

    def build_realtime_prediction_df(self, pair: str) -> pd.DataFrame:
        predict_df = None
        if not self.states["trades"].empty:
            pair_df = (
                self.states["trades"][self.states["trades"]["pair"] == pair]
                .drop(columns=["pair"])
                .reset_index(drop=True)
                # .astype(float)
            )
            ts_most_recent = max(pair_df["ts"]) - self._ops_frequency * 2 * 60
            most_recent_idx = pair_df[pair_df["ts"] > ts_most_recent].iloc[0].name
            if most_recent_idx == 0:
                logger.info(f"Not enough data gathered to run prediction for {pair}")
                return predict_df
            if (
                max(pair_df["ts"]) - pair_df.iloc[most_recent_idx]["ts"]
            ) < self._ops_frequency * 2 * 60:
                most_recent_idx -= 1
                predict_df = pair_df.iloc[most_recent_idx:]
            else:
                predict_df = pair_df
        return predict_df

    def kline_prediction(self, pair: str) -> pd.DataFrame:
        pair_df = pd.DataFrame(columns=["ts", "price", "vol", "pair"])
        interval_dict = {
            1: cts.KLINE_INTERVAL_MINUTES_1,
            3: cts.KLINE_INTERVAL_MINUTES_3,
            5: cts.KLINE_INTERVAL_MINUTES_5,
            15: cts.KLINE_INTERVAL_MINUTES_15,
            30: cts.KLINE_INTERVAL_MINUTES_30,
            60: cts.KLINE_INTERVAL_HOURS_1,
            120: cts.KLINE_INTERVAL_HOURS_2,
        }
        if self._ops_frequency not in interval_dict.keys():
            logger.error(
                f"Cannot perform auxiliary kline predictions: \
                operation frequency ({self._ops_frequency}m) is not a valid kline interval."
            )
        start_time = (
            floor(dtt.now().timestamp() - (self._ops_frequency * 4 * 60)) * 1000
        )
        kline_data = self.binance.market_data.kline_candlestick_data(
            symbol=pair,
            interval=interval_dict[self._ops_frequency],
            start_time=start_time,
            end_time=floor(dtt.now().timestamp()) * 1000,
            limit=1000,
        )["content"]
        for i, kline in enumerate(kline_data):
            close_time = kline[6] / 1000
            average_price = (float(kline[2]) + float(kline[3])) / 2
            volume = float(kline[5])
            pair_df.loc[i] = [close_time, average_price, volume, pair]
        return pair_df

    def run_prediction(self):
        for pair in self.states["pairs"]["pair"]:
            predict_df = self.build_realtime_prediction_df(pair)
            if predict_df is None:
                logger.info(
                    f"Not enough realtime data for {pair}.\
                    Attempting to predict from klines..."
                )
                predict_df = self.kline_prediction(pair)
                if predict_df is None or predict_df.empty:
                    logger.error(f"Failed to kline-predict for {pair}")
                    continue
            logging.info(f"Performing prediction for pair {pair}")
            results = self.predictor.predict(
                df_test=predict_df,
                max_price=self.states["max_prices_vols"][pair]["max_price"],
                max_vol=self.states["max_prices_vols"][pair]["max_vol"],
            )
            if results is None:
                continue
            results["prediction"] = (
                results[f"prediction_t+{self._future_periods}"].values
                * self.states["max_prices_vols"][pair]["max_price"]
            )
            results["ts"] = (  # when the predicted is bound to happen
                results.index
                + timedelta(minutes=self._ops_frequency * self._future_periods)
            ).values.astype(np.int64) // 10 ** 9
            results["pair"] = pair
            results["represents"] = self._determine_represents(
                results[["price", f"prediction_t+{self._future_periods}"]]
            )
            last_idx = len(self.states["pred_results"])
            next_last_idx = last_idx + len(results)
            self.states["pred_results"] = self.states["pred_results"].append(
                results[["ts", "prediction", "pair", "represents"]]
            )

            # logger.info(f"LATEST PREDICTION RESULTS {pair}: \n{results.tail(3)}")
        self._calculate_prediction_errors()

    def _find_time_relevant_actual_and_predictions(self):
        beginning = min(self.states["pred_results"]["ts"])
        end = max(self.states["trades"]["ts"])
        predictions = self.states["pred_results"][
            (self.states["pred_results"]["ts"] > beginning)
            & (self.states["pred_results"]["ts"] < end)
        ]
        actuals = self.states["trades"][
            (self.states["trades"]["ts"] > beginning)
            & (self.states["trades"]["ts"] < end)
        ]
        return predictions, actuals

    def _calculate_prediction_errors(self):
        if self.states["pred_results"].empty or self.states["trades"].empty:
            return
        predictions, actuals = self._find_time_relevant_actual_and_predictions()
        if predictions.empty or actuals.empty:
            logger.error("Can't calculate predictions error due to lack of data.")
            return
        for pair in self.states["pairs"]["pair"]:
            actual_pair_df = actuals[actuals["pair"] == pair][["ts", "price"]].astype(
                float
            )
            predictions_pair_df = predictions[predictions["pair"] == pair][
                ["ts", "prediction"]
            ].astype(float)
            if actual_pair_df.empty or predictions_pair_df.empty:
                logger.info(f"Can't evaluate prediction performance for {pair}")
                self.states["pred_errors"].loc[pair] = [float("nan"), float("nan")]
                continue
            rmse, mae = self.predictor.calculate_errors(
                actual_pair_df, predictions_pair_df
            )
            self.states["pred_errors"].loc[pair] = [rmse, mae]
        logger.info(
            f"CURRENT PREDICTION ERRORS:\n{self.states['pred_errors'].head(10)}"
        )

    def _determine_represents(self, joint):
        represents = []
        for i, row in joint.iterrows():
            if row[f"prediction_t+{self._future_periods}"] > row["price"] * 1.00075:
                represents.append("increase")
            elif row[f"prediction_t+{self._future_periods}"] < row["price"]:
                represents.append("decrease")
            else:
                represents.append("no_change")
        return represents
