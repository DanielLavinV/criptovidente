import cryptocompare
import datetime
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("xbteur.csv", sep=";", index_col=0)
df = df.set_index(pd.to_datetime(df.index, unit="s"))
df = df.set_index(df["timestamp"])
df = df.drop(columns=["timestamp"])
df = df[["price"]].resample("15Min").mean()
plt.plot(df.index, df["price"])
plt.show()