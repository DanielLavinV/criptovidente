from crypto_predictors.sgd import SGDPredictor
import logging
from datetime import timedelta
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PredictionsManager:
    def __init__(self, ops_freq, future_periods, ops_time_unit, states):
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

    def run_prediction(self):
        for pair in self.states["pairs"]["pair"]:
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
                continue
            if (
                max(pair_df["ts"]) - pair_df.iloc[most_recent_idx]["ts"]
            ) < self._ops_frequency * 2 * 60:
                most_recent_idx -= 1
                predict_df = pair_df.iloc[most_recent_idx:]
            else:
                predict_df = pair_df
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
        if self.states["pred_results"].empty:
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
