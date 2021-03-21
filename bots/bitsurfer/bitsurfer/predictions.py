from crypto_predictors.sgd import SGDPredictor
import logging
from math import floor
from datetime import timedelta
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PredictionsManager:
    def __init__(
        self,
        messages,
        pairs,
        ops_freq,
        trades_df,
        pred_results_df,
        pred_errors_df,
        future_periods,
        max_prices_vols,
        ops_time_unit,
    ):
        self._messages = messages
        self._trades_df = trades_df
        self._pairs = pairs
        self._ops_frequency = ops_freq
        self._prediction_results_df = pred_results_df
        self._future_periods = future_periods
        self._max_pair_prices_vols = max_prices_vols
        self._prediction_errors_df = pred_errors_df
        self._ops_time_unit = ops_time_unit
        self.predictor = SGDPredictor(
            batch_size_mins=self._ops_frequency,
            train_data_path="../data/",
            future_periods=self._future_periods,
            ops_time_unit=self._ops_time_unit,
        )

    def run_prediction(self):
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
