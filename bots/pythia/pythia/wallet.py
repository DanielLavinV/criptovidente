import pandas as pd
from os import listdir
from datetime import datetime as dtt
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WalletManager:
    def __init__(self, client, states):
        self.binance = client
        self.states = states
        self._wallet_history_file = "wallet_history.csv"

    def update_balances(self):
        logger.info("Updating account balances...")
        r = self.binance.spot_account_trade.account_information()["content"]
        balances = {}
        for b in r["balances"]:
            if float(b["free"]) == 0 and float(b["locked"]) == 0:
                continue
            balances[b["asset"]] = float(b["free"])
        self.states["balances"] = balances

    def fetch_trading_rules(self):
        logger.info("Fetching trading rules...")
        trade_rules = {}
        r = self.binance.market_data.exchange_information()
        for symbol in r["content"]["symbols"]:
            pair = symbol["symbol"]
            trade_rules[pair] = {}
            for feelter in symbol["filters"]:
                filter_type = feelter["filterType"]
                trade_rules[pair][filter_type] = {}
                for part in feelter.keys():
                    if part == "filterType":
                        continue
                    value = feelter[part]
                    if type(value) == str:
                        value = float(value)
                    trade_rules[pair][filter_type][part] = value
        self.states["trade_rules"] = trade_rules
