import pandas as pd
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import os

count = 0
reg = SGDRegressor()
predict_for = "NANOUSD.csv"
batch_size = "15T"
stop = pd.to_datetime("2020-08-01", format="%Y-%m-%d")


for pair_csv in os.listdir("./data"):
    pair_path = "./data/" + pair_csv
    df = pd.read_csv(pair_path, sep=",", names=["ts", "price", "vol"])
    df["datetime"] = pd.to_datetime(df["ts"], unit="s")
    df = df.set_index("datetime")
    df_test = df[df.index >= stop]
    df = df[df.index < stop]
    if df.empty:
        continue
        # df = df_test

    # train df
    ts_df = df[["ts"]].resample(batch_size).mean()
    price_df = df[["price"]].resample(batch_size).mean().fillna(0)
    vol_df = df[["vol"]].resample(batch_size).sum().fillna(0)
    resampled_df = pd.DataFrame(index=ts_df.index)
    resampled_df["price"] = price_df["price"].values / max(price_df["price"].values)
    resampled_df["vol"] = vol_df["vol"].values / max(vol_df["vol"].values)
    resampled_df = resampled_df.loc[(resampled_df[["price", "vol"]] != 0).any(axis=1)]
    resampled_df["price_t-1"] = resampled_df.shift(1)["price"]
    resampled_df["price_t-2"] = resampled_df.shift(2)["price"]
    resampled_df["vol_t-1"] = resampled_df.shift(1)["vol"]
    resampled_df["vol_t-2"] = resampled_df.shift(2)["vol"]
    resampled_df["target"] = resampled_df.shift(-1)["price"]
    resampled_df = resampled_df.dropna()

    # test df
    if pair_csv == predict_for:
        ts_df = df_test[["ts"]].resample(batch_size).mean()
        price_df = df_test[["price"]].resample(batch_size).mean().fillna(0)
        vol_df = df_test[["vol"]].resample(batch_size).sum().fillna(0)
        resampled_test_df = pd.DataFrame(index=ts_df.index)
        resampled_test_df["price"] = price_df["price"].values / max(
            price_df["price"].values
        )
        resampled_test_df["vol"] = vol_df["vol"].values / max(vol_df["vol"].values)
        resampled_test_df = resampled_test_df.loc[
            (resampled_test_df[["price", "vol"]] != 0).any(axis=1)
        ]
        resampled_test_df["price_t-1"] = resampled_test_df.shift(1)["price"]
        resampled_test_df["price_t-2"] = resampled_test_df.shift(2)["price"]
        resampled_test_df["vol_t-1"] = resampled_test_df.shift(1)["vol"]
        resampled_test_df["vol_t-2"] = resampled_test_df.shift(2)["vol"]
        # resampled_test_df["target"] = resampled_test_df.shift(-1)["price"]
        actual_df = resampled_test_df[["price"]]
        resampled_test_df = resampled_test_df.dropna()
        features = resampled_test_df[
            ["price", "vol", "price_t-1", "price_t-2", "vol_t-1", "vol_t-2"]
        ]
        predict_df = features

    # TRAINING
    features = resampled_df[
        ["price", "vol", "price_t-1", "price_t-2", "vol_t-1", "vol_t-2"]
    ]
    target = resampled_df["target"]
    reg.partial_fit(X=features, y=target)
    print(resampled_df.tail())

results = pd.DataFrame(index=predict_df.index)
results["prediction"] = reg.predict(X=predict_df)
results["actual"] = actual_df["price"]
rmse = mean_squared_error(
    squared=False, y_true=results["actual"], y_pred=results["prediction"]
)
mae = mean_absolute_error(y_true=results["actual"], y_pred=results["prediction"])
print(results.head())
print(f"RMSE: {rmse}")
print(f"MAE: {mae}")
plt.plot(results.index, results["actual"], color="green")
plt.plot(results.index, results["prediction"], color="blue")
plt.show()
