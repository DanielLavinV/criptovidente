import pandas as pd

features = [
    "ts",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "number_of_trades",
    "pair",
]

data_folder = "../../bnndata"


def csv_to_df(csv):
    df = pd.read_csv(f"{data_folder}/{csv}", sep=",", names=features)
    df["pair"] = csv.replace(".csv", "")
    return df


def group_df_by_pair(pair, bnn_data):
    pass


def normalize_df(pair_df):
    max_price = max(pair_df.high)
    max_vol = max(pair_df.volume)
    max_q_vol = max(pair_df.quote_volume)
    max_not = max(pair_df.number_of_trades)
    pair_df["open"] = pair_df["open"] / max_price
    pair_df["high"] = pair_df["high"] / max_price
    pair_df["low"] = pair_df["low"] / max_price
    pair_df["close"] = pair_df["close"] / max_price
    pair_df["volume"] = pair_df["volume"] / max_vol
    pair_df["quote_volume"] = pair_df["quote_volume"] / max_q_vol
    pair_df["number_of_trades"] = pair_df["number_of_trades"] / max_not
    pair_df = pair_df.drop(columns=["pair"])
    return pair_df


def calculate_extra_features(pair_df):
    pair_df.avg_price = (pair_df.high + pair_df.low + pair_df.open + pair_df.close) / 4
    pair_df.spread = pair_df.high - pair_df.low
    pair_df.change = pair_df.open - pair_df.close
    pair_df.change_pct = (pair_df.change / pair_df.avg_price) * 100
    return pair_df
