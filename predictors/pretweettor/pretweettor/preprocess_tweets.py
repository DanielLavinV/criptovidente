"""
GOAL: Perform the following preprocessing/normalization procedures on clean tweets:
            1. Stop-words removal
            2. Stemming
            3. Lemmatization
            4. Spelling correction
"""
import string
import os
import pandas as pd
from nltk.corpus import stopwords
import re
from langdetect import detect
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize


def url_removal(df):
    for idx, row in df.iterrows():
        text = row["text"]
        text = text.replace("pic.twitter", "http://pic.twitter")
        text = text.replace("https", "http")
        text = text.replace("http:", " http:")
        text = re.sub(r"http\S+", "", text, flags=re.MULTILINE)
        text = re.sub(" +", " ", text)
        text = text.replace("\n", " ")
        row["text"] = text
    return df


def noise_removal(df):
    special_chars = string.punctuation
    for idx, row in df.iterrows():
        row["text"] = row["text"].translate({ord(i): None for i in special_chars})
    return df


def lowercasing(df):
    for idx, row in df.iterrows():
        row["text"] = row["text"].lower()
    return df


def number_removal(df):
    special_chars = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
    for idx, row in df.iterrows():
        row["text"] = row["text"].translate({ord(i): None for i in special_chars})
    return df


# Will also remove words shorter than 2 letters
def stop_words_removal(df):
    stop_words = set(stopwords.words("english"))
    for idx, row in df.iterrows():
        dirty_words = row["text"].split(" ")
        words = [w for w in dirty_words if (w not in stop_words and len(w) > 1)]
        row["text"] = " ".join(words)
    return df


def ticker_symbol_removal(df):
    ticker_symbols = [
        "xbt",
        "btc",
        "eth",
        "ltc",
        "xrp",
        "bch",
        "usd",
        "eur",
        "dbix",
        "bnb",
        "bat",
        "xlm",
        "ada",
        "trx",
        "gbp",
        "aud",
        "nzd",
        "cny",
        "chf",
        "mxn",
        "icx",
    ]
    for idx, row in df.iterrows():
        words = row["text"].split(" ")
        cleaned = [w for w in words if w not in ticker_symbols]
        row["text"] = " ".join(cleaned)
    return df


def remove_nonenglish(df):
    drop_idxs = []
    df = df.reset_index(drop=True)
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(idx)
        try:
            lan = detect(row["text"])
            if lan != "en":
                drop_idxs.append(idx)
        except TypeError as e:
            pass
    df = df.drop(index=drop_idxs)
    return df


def null_removal(df):
    drop_idxs = []
    for idx, row in df.iterrows():
        if not row["text"]:
            drop_idxs.append(idx)
    df = df.drop(index=drop_idxs)
    return df


def short_entries_removal(df):
    drop_idxs = []
    for idx, row in df.iterrows():
        if len(row["text"].split(" ")) < 4:
            drop_idxs.append(idx)
    df = df.drop(index=drop_idxs)
    return df


def perform_lemmatization(df):
    lemmatizer = WordNetLemmatizer()
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(idx, end=" ")
        text = row["text"]
        if "’" in text:
            text = text.replace("’", "'")
        if "“" in text:
            text = text.replace("“", "")
        if "”" in text:
            text = text.replace("”", "")
        words = word_tokenize(text)
        lemmatized_words = []
        for word in words:
            lemmatized_words.append(lemmatizer.lemmatize(word))
        row["text"] = " ".join(lemmatized_words)
    return df


# with open("./../data/clean_tweets.csv") as f, open("preprocessed_tweets.csv", "w+") as of:
with open("preprocessed_tweets.csv") as f, open("lemmatized_tweets.csv", "w+") as of:
    print("reading csv...")
    df = pd.read_csv(f, index_col=0, sep=";", engine="python", error_bad_lines=False)
    print(f"({df.shape[0]}) removing urls and whitespace")
    df = url_removal(df)
    print(f"({df.shape[0]}) removing noise...")
    df = noise_removal(df)
    print(f"({df.shape[0]}) lowercasing...")
    df = lowercasing(df)
    print(f"({df.shape[0]}) removing numbers...")
    df = number_removal(df)
    print(f"({df.shape[0]}) removing stop words...")
    df = stop_words_removal(df)
    print(f"({df.shape[0]}) removing ticker symbols...")
    df = ticker_symbol_removal(df)
    print(f"({df.shape[0]}) removing empty entries...")
    df = null_removal(df)
    print(f"({df.shape[0]}) removing remaining nonenglish tweets...")
    df = remove_nonenglish(df)
    print(f"({df.shape[0]}) removing short entries...")
    df = short_entries_removal(df)
    print("Performing lemmatization...")
    df = perform_lemmatization(df)
    print(f"({df.shape[0]}) writing output...")
    df.to_csv(of, sep=";")
