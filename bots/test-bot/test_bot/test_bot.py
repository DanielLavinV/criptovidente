import pandas as pd
from numeric_predictors.predictions import simple_linear_regression
import matplotlib.pyplot as plt
import math
import random
import numpy as np
from typing import List
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, mean_squared_error


def get_random_chunk(df: pd.DataFrame, steps: int, step_size: int) -> pd.DataFrame:
    first_ts = min(df.index)
    max_ts = max(df.index)
    period_size = steps * step_size
    not_after = max_ts - period_size
    beginning = random.randint(first_ts, not_after)
    end = beginning + period_size
    return df[(beginning <= df.index) & (df.index < end)]


def angle_of_change(cx: float, cy: float, ex: float, ey: float) -> float:
    dy = ey - cy
    dx = ex - cx
    theta = math.atan(dy / dx)
    return theta * 180 / math.pi


def determine_confusion(fca: float, aca: float):
    threshold = 0.0
    if aca > threshold:
        a = "increase"
    elif -threshold <= aca and aca <= threshold:
        a = "no_change"
    else:
        a = "decrease"
    if fca > threshold:
        f = "increase"
    elif -threshold <= fca and fca <= threshold:
        f = "no_change"
    else:
        f = "decrease"
    return f, a


def operate_with_sln(df: pd.DataFrame, steps: int, step_sizes: List[int]):
    list_of_results = []
    rmse_list = []
    confusion_list = []
    possible_change_forecasts = ["no_change", "increase", "decrease"]
    for step_size in step_sizes:
        local_price_forecast_results = pd.DataFrame(
            columns=["forecast", "actual", "timestamp"]
        )
        local_change_forecast_results = pd.DataFrame(columns=["forecast", "actual"])
        df = get_random_chunk(df, steps, step_size)
        chunk_1s_resample = df
        chunk_1s_resample["timestamp"] = chunk_1s_resample.index
        chunk_1s_resample["datetime"] = pd.to_datetime(df.index)
        chunk_1s_resample = df.set_index("datetime").resample("1s").mean()
        chunk_1s_resample = chunk_1s_resample.set_index(
            "timestamp"
        )  # this DF will give you the actual measurement but at the 1-second-step-mark
        init_ts = min(df.index)
        first_ts = init_ts
        last_ts = max(df.index)
        # steps = math.floor((last_ts-init_ts) / step_size) - 1
        for i in range(0, steps):
            print(f"{i}/{steps}")
            next_edge = init_ts + step_size
            next_future_edge = next_edge + step_size
            sln_datapoints = df[(init_ts < df.index) & (df.index < next_edge)]
            forecast_time = df[
                (next_edge < df.index) & (df.index < next_future_edge)
            ].index
            # print(sln_datapoints.head())
            # print(forecast_time)
            if sln_datapoints.empty or forecast_time.empty:
                init_ts = next_edge
                continue
            forecast_vals = simple_linear_regression(
                x_learn=sln_datapoints.index.values,
                y_learn=sln_datapoints["price"].values,
                x_predict=np.array([next_future_edge]),
            )
            present_vals = simple_linear_regression(
                x_learn=sln_datapoints.index.values,
                y_learn=sln_datapoints["price"].values,
                x_predict=np.array([next_edge]),
            )
            # Price forecast
            local_price_forecast_results.loc[i + 1, "forecast"] = forecast_vals[0]
            local_price_forecast_results.loc[i, "actual"] = present_vals[0]
            local_price_forecast_results.loc[i, "timestamp"] = next_edge
            # Increase/decrease (change) forecast
            if i != 0:
                try:
                    forecast_change_angle = angle_of_change(
                        cx=next_edge,
                        cy=local_price_forecast_results.loc[i, "forecast"],
                        ex=init_ts,
                        ey=local_price_forecast_results.loc[i - 1, "actual"],
                    )
                    actual_change_angle = angle_of_change(
                        cx=next_edge,
                        cy=local_price_forecast_results.loc[i, "actual"],
                        ex=init_ts,
                        ey=local_price_forecast_results.loc[i - 1, "actual"],
                    )
                    forecast_change, actual_change = determine_confusion(
                        forecast_change_angle, actual_change_angle
                    )
                    local_change_forecast_results.loc[i, "forecast"] = forecast_change
                    local_change_forecast_results.loc[i, "actual"] = actual_change
                except KeyError as e:
                    pass
            # plt.scatter(
            #     next_edge,
            #     present_vals[0],
            #     color="green"
            #     )
            # plt.scatter(
            #     next_future_edge,
            #     forecast_vals[0],
            #     color="blue"
            # )
            init_ts = next_edge
    print(local_price_forecast_results.sort_index().head())
    plt.plot(
        local_price_forecast_results["timestamp"],
        local_price_forecast_results["actual"],
        color="green",
    )
    plt.plot(
        local_price_forecast_results["timestamp"],
        local_price_forecast_results["forecast"],
        color="blue",
    )
    plt.vlines(
        x=range(first_ts, next_edge, step_size),
        ymin=min(local_price_forecast_results["forecast"]) - 50,
        ymax=max(local_price_forecast_results["forecast"]) + 50,
        colors="black",
    )

    plt.figure(2)
    plt.scatter(
        local_price_forecast_results["forecast"], local_price_forecast_results["actual"]
    )
    confusion_mtx = confusion_matrix(
        y_true=local_change_forecast_results["actual"],
        y_pred=local_change_forecast_results["forecast"],
        labels=possible_change_forecasts,
    )
    confusion_mtx_disp = ConfusionMatrixDisplay(
        confusion_matrix=confusion_mtx, display_labels=possible_change_forecasts
    )
    confusion_mtx_disp.plot()
    nc_nc, nc_i, nc_d, i_nc, i_i, i_d, d_nc, d_i, d_d = confusion_mtx.ravel()
    price_change_accuracy = (nc_nc + i_i + d_d) / (
        nc_nc + nc_i + nc_d + i_nc + i_i + i_d + d_nc + d_i + d_d
    )
    print(f"Accuracy: {price_change_accuracy*100}%")
    plt.show()


df1 = pd.read_csv("../../../predictors/data/btc_prices_eur.csv", sep=";")


# df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
# print(df.head())
# df = df.set_index("datetime")
# df = df.resample("5T").mean()
# print(df.head())


df1 = df1.set_index("timestamp")
operate_with_sln(df=df1, steps=5000, step_sizes=[60 * 10])

# print(angle_of_change(cx=5, cy=-5, ex=0, ey=0))
