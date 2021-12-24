import pandas as pd
from numpy import isinf
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os
import logging
from datetime import datetime as dtt

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
        past_periods: int = 2,
    ):
        self.reggressors = {"avg_price": SGDRegressor(), "spread": SGDRegressor()}
        self._batch_size = f"{batch_size_mins}{ops_time_unit}"
        self._train_data_path = train_data_path
        self._future_periods = future_periods
        self._past_periods = past_periods
        logger.info("Training SGD model...")
        self._train()

    def _train(self):
        for pair_csv in os.listdir(self._train_data_path):
            pair_path = self._train_data_path + pair_csv
            # df = pd.read_csv(pair_path, sep=",", names=["ts", "price", "vol"])
            df = pd.read_csv(
                pair_path,
                sep=",",
                names=[
                    "ts",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "quote_volume",
                    "number_of_trades",
                ],
            )
            if df.empty:
                continue
            df["datetime"] = pd.to_datetime(df["ts"], unit="ms")
            df = df.set_index("datetime")
            ts_df = df[["ts"]].resample(self._batch_size).first()
            open_df = df[["open"]].resample(self._batch_size).first()
            high_df = df[["high"]].resample(self._batch_size).max()
            low_df = df[["low"]].resample(self._batch_size).min()
            close_df = df[["close"]].resample(self._batch_size).last()
            q_vol_df = df[["quote_volume"]].resample(self._batch_size).sum()
            n_o_t_df = df[["number_of_trades"]].resample(self._batch_size).sum()
            resampled_df = pd.DataFrame(index=ts_df.index)
            max_price = max(high_df["high"].values)
            resampled_df["open"] = open_df["open"].values / max_price
            resampled_df["high"] = high_df["high"].values / max_price
            resampled_df["low"] = low_df["low"].values / max_price
            resampled_df["close"] = close_df["close"].values / max_price
            resampled_df["quote_volume"] = q_vol_df["quote_volume"].values / max(
                q_vol_df["quote_volume"].values
            )
            resampled_df["number_of_trades"] = n_o_t_df[
                "number_of_trades"
            ].values / max(n_o_t_df["number_of_trades"].values)
            cols = resampled_df.columns[:]
            for col in cols:
                for i in range(1, self._past_periods + 1):
                    resampled_df[f"{col}_t-{i}"] = resampled_df[col].shift(i)
            resampled_df = resampled_df.dropna()
            resampled_df["avg_price"] = (
                resampled_df["open"]
                + resampled_df["close"]
                + resampled_df["low"]
                + resampled_df["high"]
            ) / 4
            resampled_df["spread"] = resampled_df["high"] - resampled_df["low"]
            resampled_df["target_avg_price"] = resampled_df["avg_price"].shift(
                -self._future_periods
            )
            resampled_df["target_spread"] = resampled_df["spread"].shift(
                -self._future_periods
            )
            resampled_df = resampled_df.dropna()
            # TRAINING
            features = [
                "open",
                "close",
                "low",
                "high",
                "quote_volume",
                "number_of_trades",
            ]
            features.extend([col for col in resampled_df.columns if "t-" in col])
            features_df = resampled_df[features]
            for target in ["avg_price", "spread"]:
                target_df = resampled_df[f"target_{target}"]
                try:
                    self.reggressors[target].partial_fit(X=features_df, y=target_df)
                except Exception as e:
                    logger.info(f"Exception when training: {e}")
                    print(e)
                    print(f"PAIR: {pair_csv}, FEATURES:\n{features_df.head(20)}")
        logger.info("SGD Model training complete.")

    def predict(
        self, df: pd.DataFrame, max_price: float, max_quote_vol: float, max_not: int
    ):
        df["datetime"] = pd.to_datetime(df["ts"], unit="ms")
        df = df.set_index("datetime")
        ts_df = df[["ts"]].resample(self._batch_size).first()
        open_df = df[["open"]].resample(self._batch_size).first()
        high_df = df[["high"]].resample(self._batch_size).max()
        low_df = df[["low"]].resample(self._batch_size).min()
        close_df = df[["close"]].resample(self._batch_size).last()
        q_vol_df = df[["quote_volume"]].resample(self._batch_size).sum()
        n_o_t_df = df[["number_of_trades"]].resample(self._batch_size).sum()
        resampled_df = pd.DataFrame(index=ts_df.index)
        resampled_df["open"] = open_df["open"].values / max_price
        resampled_df["high"] = high_df["high"].values / max_price
        resampled_df["low"] = low_df["low"].values / max_price
        resampled_df["close"] = close_df["close"].values / max_price
        resampled_df["quote_volume"] = q_vol_df["quote_volume"].values / max_quote_vol
        resampled_df["number_of_trades"] = n_o_t_df["number_of_trades"].values / max_not
        cols = resampled_df.columns[:]
        for col in cols:
            for i in range(1, self._past_periods + 1):
                resampled_df[f"{col}_t-{i}"] = resampled_df[col].shift(i)
        resampled_df = resampled_df.dropna()
        resampled_df["avg_price"] = (
            resampled_df["open"]
            + resampled_df["close"]
            + resampled_df["low"]
            + resampled_df["high"]
        ) / 4
        resampled_df["spread"] = resampled_df["high"] - resampled_df["low"]
        resampled_df["target_avg_price"] = resampled_df["avg_price"].shift(
            -self._future_periods
        )
        resampled_df["target_spread"] = resampled_df["spread"].shift(
            -self._future_periods
        )
        resampled_df = resampled_df.dropna()
        features = ["open", "close", "low", "high", "quote_volume", "number_of_trades"]
        features.extend([col for col in resampled_df.columns if "t-" in col])
        predict_df = resampled_df[features]
        results = pd.DataFrame(index=predict_df.index)
        for target in ["avg_price", "spread"]:
            results[f"pred_{target}_t+{self._future_periods}"] = self.reggressors[
                target
            ].predict(X=predict_df)
            results[f"pred_{target}_t+{self._future_periods}"] = (
                results[f"pred_{target}_t+{self._future_periods}"] * max_price
            )
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
            if row["prediction"] > row["price"] * 1.05:
                represents.append("increase")
            if row["prediction"] < row["price"]:
                represents.append("decrease")
            else:
                represents.append("no_change")
        return represents
