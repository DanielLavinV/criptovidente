import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import List


class Animator:
    def __init__(
        self,
        pred_df: pd.DataFrame,
        actual_df: pd.DataFrame,
        animation_interval: int,
        number_of_plots: int,
        pairs: List[str],
        ops_freq: int,
    ):
        self._animation_interval = animation_interval
        self._number_of_plots = number_of_plots
        self._fig = plt.figure()
        self._pred_df = pred_df
        self._actual_df = actual_df
        self._batch_size = f"{ops_freq}T"
        self._pairs = pairs
        self._generate_pair_df_plot_dict()

    def _generate_pair_df_plot_dict(self):
        self._plots = {}
        for i, pair in enumerate(self._pairs):
            self._plots[pair] = self._fig.add_subplot(
                len(self._pairs), 1, i + 1, ylabel=pair
            )

    def _animate(self, i):
        for pair in self._pairs:
            actual = self._actual_df[self._actual_df["pair"] == pair]
            actual["datetime"] = pd.to_datetime(actual["ts"], unit="s")
            actual = actual.set_index("datetime").resample(self._batch_size).mean()
            pred = self._pred_df[self._pred_df["pair"] == pair]
            pred["datetime"] = pd.to_datetime(pred["ts"], unit="s")
            pred = pred.set_index("datetime").resample(self._batch_size).mean()
            joint = pd.merge(
                actual, pred, how="inner", right_index=True, left_index=True
            ).dropna()
            self._plots[pair].clear()
            self._plots[pair].plot(joint.index, joint["price"], color="green")
            self._plots[pair].plot(joint.index, joint["prediction"], color="blue")

    def run(self):
        self._animation = animation.FuncAnimation(
            self._fig, self._animate, interval=self._animation_interval
        )
        plt.show()
