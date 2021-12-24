import pandas as pd
from crypto_predictors.sgd import SGDPredictor
import matplotlib.pyplot as plt

test_pair = "DOGEBTC"

df = pd.read_csv(
    "DOGEBTC.csv",
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
df["datetime"] = pd.to_datetime(df["ts"], unit="ms")
df = df.set_index("datetime")
df["spread"] = df["high"] - df["low"]
df["avg_price"] = (df["open"] + df["close"] + df["low"] + df["high"]) / 4

reg = SGDPredictor(
    batch_size_mins=15 * 484, train_data_path="./bnndata/", ops_time_unit="T"
)

res = reg.predict(
    df=df,
    max_price=max(df["high"]),
    max_quote_vol=max(df["quote_volume"]),
    max_not=max(df["number_of_trades"]),
)

print(f"DF: \n{df[['avg_price', 'spread']].head(10)}")
print(f"RES: \n{res.head(10)}")
fig = plt.figure()
plt.plot(df.index, df.spread, color="green")
plt.plot(res.index, res["pred_spread_t+1"], color="blue")
fig2 = plt.figure()
plt.plot(df.index, df.avg_price, color="green")
plt.plot(res.index, res["pred_avg_price_t+1"], color="blue")
plt.show()
