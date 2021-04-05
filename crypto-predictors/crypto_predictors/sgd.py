import pandas as pd
from numpy import isinf
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os
import logging

pd.options.mode.chained_assignment = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TIMEZONE = "Europe/Berlin"


class SGDPredictor:
    def __init__(
        self,
        batch_size_mins: int,
        train_data_path: str,
        ops_time_unit: str,
        future_periods: int = 1,
    ):
        self.reggressor = SGDRegressor()
        self._batch_size = f"{batch_size_mins}{ops_time_unit}"
        self._train_data_path = train_data_path
        self._future_periods = future_periods
        logger.info("Training SGD model...")
        self._train()

    def _train(self):
        for pair_csv in os.listdir(self._train_data_path):
            pair_path = self._train_data_path + pair_csv
            df = pd.read_csv(pair_path, sep=",", names=["ts", "price", "vol"])
            df["datetime"] = pd.to_datetime(df["ts"], unit="s")
            df = df.set_index("datetime")
            if df.empty:
                continue
            ts_df = df[["ts"]].resample(self._batch_size).mean()
            price_df = df[["price"]].resample(self._batch_size).mean().fillna(0)
            vol_df = df[["vol"]].resample(self._batch_size).sum().fillna(0)
            resampled_df = pd.DataFrame(index=ts_df.index)
            resampled_df["price"] = price_df["price"].values / max(
                price_df["price"].values
            )
            resampled_df["vol"] = vol_df["vol"].values / max(vol_df["vol"].values)
            resampled_df["price_t-1"] = resampled_df.shift(1)["price"]
            resampled_df["price_t-2"] = resampled_df.shift(2)["price"]
            resampled_df["vol_t-1"] = resampled_df.shift(1)["vol"]
            resampled_df["vol_t-2"] = resampled_df.shift(2)["vol"]
            resampled_df["target"] = resampled_df.shift(-self._future_periods)["price"]
            resampled_df = resampled_df.loc[
                (resampled_df[["price", "vol"]] != 0).any(axis=1)
            ]
            resampled_df = resampled_df.loc[
                (resampled_df[["price_t-1", "vol_t-1"]] != 0).any(axis=1)
            ]
            resampled_df = resampled_df.loc[
                (resampled_df[["price_t-2", "vol_t-2"]] != 0).any(axis=1)
            ]
            resampled_df = resampled_df.loc[(resampled_df[["target"]] != 0).any(axis=1)]
            resampled_df = resampled_df.dropna()
            # TRAINING
            features = resampled_df[
                ["price", "vol", "price_t-1", "price_t-2", "vol_t-1", "vol_t-2"]
            ]
            target = resampled_df["target"]
            self.reggressor.partial_fit(X=features, y=target)
        logger.info("SGD Model training complete.")

    def predict(self, df_test: pd.DataFrame, max_price: float, max_vol: float):
        df_test["datetime"] = pd.to_datetime(df_test["ts"], unit="s")
        df_test = df_test.set_index("datetime")
        ts_df = df_test[["ts"]].resample(self._batch_size).mean()
        price_df = df_test[["price"]].resample(self._batch_size).mean().fillna(0)
        vol_df = df_test[["vol"]].resample(self._batch_size).sum().fillna(0)
        resampled_test_df = pd.DataFrame(index=ts_df.index)
        resampled_test_df["price"] = price_df["price"].values / max_price
        resampled_test_df["vol"] = vol_df["vol"].values / max_vol
        resampled_test_df = resampled_test_df.loc[
            (resampled_test_df[["price", "vol"]] != 0).any(axis=1)
        ]
        resampled_test_df["price_t-1"] = resampled_test_df.shift(1)["price"]
        resampled_test_df["price_t-2"] = resampled_test_df.shift(2)["price"]
        resampled_test_df["vol_t-1"] = resampled_test_df.shift(1)["vol"]
        resampled_test_df["vol_t-2"] = resampled_test_df.shift(2)["vol"]
        actual_df = resampled_test_df[["price"]]
        resampled_test_df = resampled_test_df.dropna()
        features = resampled_test_df[
            ["price", "vol", "price_t-1", "price_t-2", "vol_t-1", "vol_t-2"]
        ]
        if features.empty:
            logger.error("Insufficient data gathered to run prediction.")
            return None
        predict_df = features
        results = pd.DataFrame(index=predict_df.index)
        results[f"prediction_t+{self._future_periods}"] = self.reggressor.predict(
            X=predict_df
        )
        results["price"] = features["price"]
        return results

    def forge_joint_dataframe_for_errors(
        self, actual: pd.DataFrame, pred: pd.DataFrame
    ):
        # logger.info("Calculating prediction error...")
        actual["datetime"] = pd.to_datetime(actual["ts"], unit="s").dt.tz_localize(
            TIMEZONE, ambiguous=True, nonexistent="shift_forward"
        )  # .dt.tz_convert(TIMEZONE)
        actual = actual.set_index("datetime").resample(self._batch_size).mean()
        pred["datetime"] = pd.to_datetime(pred["ts"], unit="s").dt.tz_localize(
            TIMEZONE, ambiguous=True, nonexistent="shift_forward"
        )  # .dt.tz_convert(TIMEZONE)
        pred = pred.set_index("datetime").resample(self._batch_size).mean()
        joint = pd.merge(
            actual, pred, how="inner", right_index=True, left_index=True
        ).dropna()
        return joint

    def calculate_errors(self, actual: pd.DataFrame, pred: pd.DataFrame):
        joint = self.forge_joint_dataframe_for_errors(actual, pred)
        if joint.isnull().any().any():
            logger.error(
                f"Unable to calculate error: DF contains NaN: \n {joint.head()}"
            )
            return float("nan"), float("nan")
        if isinf(joint).any().any():
            logger.error(
                f"Unable to calculate error: DF contains infinity: \n {joint.head()}"
            )
            return float("nan"), float("nan")
        if joint.empty:
            logger.error(
                "Unable to calculate error: no temporal intersection between predictions and real measurements."
            )
            return float("nan"), float("nan")
        rmse = mean_squared_error(
            squared=False, y_true=joint["price"], y_pred=joint["prediction"]
        )
        mae = mean_absolute_error(y_true=joint["price"], y_pred=joint["prediction"])
        return rmse, mae

    def determine_represents(self, actual: pd.DataFrame, pred: pd.DataFrame):
        represents = []
        joint = self.forge_joint_dataframe_for_errors(actual, pred)
        if joint.isnull().any().any():
            logger.error(
                f"Unable to calculate represents: DF contains NaN: \n {joint.head()}"
            )
        if isinf(joint).any().any():
            logger.error(
                f"Unable to calculate represents: DF contains infinity: \n {joint.head()}"
            )
        if joint.empty:
            logger.error(
                "Unable to calculate represents: no temporal intersection between predictions and real measurements."
            )
        for i, row in joint.iterrows():
            if row["prediction"] > row["price"] * 1.00075:
                represents.append("increase")
            if row["prediction"] < row["price"]:
                represents.append("decrease")
            else:
                represents.append("no_change")
        return represents
