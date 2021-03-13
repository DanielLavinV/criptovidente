from binance_client.client import BinanceClient
import pandas as pd


class Bitsurfer:
    def __init__(self):
        self.binance = BinanceClient("~/.binance/keys.json", False)
        self.binance_test = BinanceClient("~/.binance/keys.json", True)

    def create_sockets(self):
        klines = self.binance()
