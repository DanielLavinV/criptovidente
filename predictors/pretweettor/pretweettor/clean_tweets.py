"""
GOAL: clean raw tweets
        1. Remove false separators from original file i.e. tweets sometimes contain the separator character ";"
        2. Remove all tweets that:
            i) are empty
            ii) come from bots
            iii) are not in the english language
        3. Write a csv file with the cleaned tweets
"""
import os
import pandas as pd
import string


class TweetCleaner:
    # original csv file with tweets contained false separators ";" used for emojis ;) or other purposes. Remove them.
    def remove_false_csv_separator(self, input_f: str, output_f: str):
        with open(input_f) as f, open(output_f, "w+") as of:
            for line in f:
                line = line.replace("; ", "")
                line = line.replace(" ;", "")
                of.write(line)

    def get_n_tweets_as_csv(self, input_f: str, output_f: str, n: int):
        with open(input_f) as f, open(output_f, "w+") as of:
            maxss = n
            for i in range(maxss):
                line = f.readline()
                of.write(line)

    def clean_tweets(self, input_f: str, output_f: str):
        allowed = string.printable + "’" + "“" + "”"
        drop_idxs = []
        df = pd.read_csv(input_f, sep=";", engine="python", error_bad_lines=False)
        df = df.dropna()
        for idx, row in df.iterrows():
            # Remove empty tweets
            if not row["text"]:
                drop_idxs.append(idx)
                continue
            # Remove tweets from bots
            if "BOT" in row["user"] or "bot" in row["user"] or "Bot" in row["user"]:
                drop_idxs.append(idx)
                continue
            if (
                "BOT" in row["fullname"]
                or "bot" in row["fullname"]
                or "Bot" in row["fullname"]
            ):
                drop_idxs.append(idx)
                continue
            # Remove nonenglish tweets
            bools = list(map(lambda c: c not in allowed, row["text"]))
            if any(bools):
                drop_idxs.append(idx)
                continue
        df = df.drop(index=drop_idxs)
        with open(output_f, "w+") as of:
            df.to_csv(of, sep=";")

    def remove_unwanted_cols(self, input_f: str, output_f: str, cols: List[str]):
        df = pd.read_csv(
            input_f, index_col=0, sep=";", engine="python", error_bad_lines=False
        )
        df = df.drop(columns=cols)
        with open(output_f, "w+") as of:
            df.to_csv(of, sep=";")


# no_false_separator_tweets.csv is in my L drive
# clean_tweets("no_false_separator_tweets.csv", "tweets.csv")
# os.remove("no_false_separator_tweets.csv")
# remove_unwanted_cols("tweets.csv", "clean_tweets.csv", ["user","fullname","url","replies","likes","retweets","id"])
# os.remove("tweets.csv")
