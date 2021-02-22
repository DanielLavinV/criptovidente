import cryptocompare
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import numpy as np

btc_prices = pd.read_csv("btc_prices_eur.csv", sep=";", index_col=0)
btc_prices = btc_prices.set_index(pd.to_datetime(btc_prices.index, unit="s"))
# btc_prices = btc_prices.set_index(btc_prices["timestamp"])
# btc_prices = btc_prices.drop(columns=["timestamp"])
btc_prices = btc_prices[["price"]].resample("15Min").mean()
btc_prices = btc_prices.set_index(btc_prices.index.values.astype(np.int64) // 10**9)
first_btc_price_ts = min(btc_prices.index) # type: timestamps.Timestamp
print(f"First btc price ts is: {first_btc_price_ts} and type is {type(first_btc_price_ts)}")

# get tweets and form 15 min batches
tweets = pd.read_csv("../data/sentimented_tweets.csv", sep=";", index_col=0)
tweets = tweets.drop(columns=["index","pos","neg","neu","text"])
tweets = tweets.set_index(tweets["timestamp"])
tweets = tweets.drop(columns=["timestamp"]) # index type: indexes.base.Index, index element type: str
tweets = tweets.set_index(pd.to_datetime(tweets.index)) #index type: indexes.datetimes.DatetimeIndex, index element type: timestamps.Timestamp
tweets = tweets.set_index(tweets.index.values.astype(np.int64) // 10**9)
print(f"Type of whole index is: {type(tweets.index)}, type of one element is: {type(tweets.index[0])}")
tweets = tweets[tweets.index > first_btc_price_ts] # TODO: convert to first_btc_price_ts from Timestamp to datetime64 to be able to make this comparison
print(f"First tweets ts is: {min(tweets.index)}")
tweets = tweets.set_index(pd.to_datetime(tweets.index, unit="s"))
pos_tweets = tweets[["comp"]].gt(0.05).groupby(pd.Grouper(freq="15Min")).sum()
neg_tweets = tweets[["comp"]].lt(-0.05).groupby(pd.Grouper(freq="15Min")).sum()
print(pos_tweets.head(10))
print(neg_tweets.head(10))

plt.plot(pos_tweets.index, pos_tweets["comp"], color="green")
plt.plot(neg_tweets.index, neg_tweets["comp"], color="red")
btc_prices = btc_prices.set_index(pd.to_datetime(btc_prices.index, unit="s"))
plt.plot(btc_prices.index, btc_prices["price"], color="black")
plt.show()