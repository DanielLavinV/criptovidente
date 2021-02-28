from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import pandas as pd

sentiment_analyzer = SentimentIntensityAnalyzer()

df = pd.read_csv(
    "./../data/lemmatized_tweets.csv", sep=";", engine="python", index_col=0
).reset_index()

for idx, row in df.iterrows():
    if idx % 100 == 0:
        print(idx, end=" ")
    analysis = sentiment_analyzer.polarity_scores(row["text"])
    df.loc[idx, "pos"] = analysis["pos"]
    df.loc[idx, "neu"] = analysis["neu"]
    df.loc[idx, "neg"] = analysis["neg"]
    df.loc[idx, "comp"] = analysis["compound"]
    if idx % 1000 == 0:
        print("\n")

with open("results.csv", "w+") as of:
    df.to_csv(of, sep=";")
