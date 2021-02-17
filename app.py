from data_fetcher.main import DataFetcher

class Criptovidente:
    def __init__(self):
        pass

    def run(self):
        fetcher = DataFetcher()
        fetcher.fetch_tweets(0,0,5)

vidente = Criptovidente()
vidente.run()