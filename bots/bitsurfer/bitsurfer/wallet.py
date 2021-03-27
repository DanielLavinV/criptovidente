import pandas as pd
from os import listdir
from datetime import datetime as dtt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WalletManager:
    def __init__(self, client, balances):
        self.binance = client
        self._wallet_history_file = "wallet_history.csv"
        self.balances = balances
        self.update_fees()
        self.update_balances()

    def update_fees(self):
        logger.info("Updating fees...")
        fees = {}
        r = self.binance.wallet.trade_fee()["content"]
        for fee in r["tradeFee"]:
            fees[fee["symbol"]] = {"maker": fee["maker"], "taker": fee["taker"]}
        self.fees = fees

    def update_balances(self):
        logger.info("Updating account balances...")
        r = self.binance.spot_account_trade.account_information()["content"]
        balances = {}
        for b in r["balances"]:
            if float(b["free"]) and float(b["locked"]) == 0:
                continue
            balances[b["asset"]] = float(b["free"])
        self.balances = balances

    def _update_wallet_history(self):
        if self.wallet_history_file in listdir("/history"):
            wallet_history = pd.read_csv(f"history/{self._wallet_history_file}")
        else:
            wallet_history = pd.DataFrame(columns=["ts", "coin", "balance"])
        for b in self.balances.keys():
            wallet_history.loc[-1] = [
                dtt.now().timestamp(),
                b,
                self.balances[b]["free"],
            ]
            wallet_history.index = wallet_history.index + 1
            wallet_history = wallet_history.sort_index()
        wallet_history.to_csv(path=f"/history/{self._wallet_history_file}")

    def generate_report(self):
        if self.wallet_history_file in listdir("/history"):
            wallet_history = pd.read_csv(f"history/{self._wallet_history_file}")
        else:
            logger.info("No wallet records to report.")
            return
        if wallet_history.shape[0] < 2:
            logger.info("No wallet records to report.")
            return
