from binance_client.client import BinanceClient
import pandas as pd
import threading
import time
import schedule
from predictions import PredictionsManager
from wallet import WalletManager
from streams import StreamsManager
from decisions import DecisionsManager
from orders import OrdersManager
from math import floor
import logging

pd.set_option("display.float_format", "{:.10f}".format)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] -%(levelname)s- | %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)


class Bitsurfer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._test_net = False
        self.binance = BinanceClient("/home/lavin/.binance/keys.json", self._test_net)
        self._ops_frequency = 3
        self._ops_time_unit = "T"
        self._future_periods = 1
        self._prediction_results_df = pd.DataFrame(
            columns=[
                "ts",
                "prediction",
                "pair",
                "represents",
            ]  # "ts" references when the prediction WILL happen
        )
        self._trades_df = pd.DataFrame(columns=["ts", "price", "vol", "pair"])
        self._prediction_errors_df = pd.DataFrame(columns=["rmse", "mae"])
        self._pairs_df = pd.DataFrame(columns=["pair", "growth"])
        # Encapsulate the state dataframes in a dictionary so that they
        # can be shared among the managers
        self._messages = []
        self._max_pair_prices_vols = {}
        self._balances = {}
        self.states = {
            "pred_results": self._prediction_results_df,
            "trades": self._trades_df,
            "pred_errors": self._prediction_errors_df,
            "pairs": self._pairs_df,
            "messages": self._messages,
            "max_prices_vols": self._max_pair_prices_vols,
            "balances": self._balances,
        }
        self._should_terminate = False
        self.predictions_manager = PredictionsManager(
            ops_freq=self._ops_frequency,
            future_periods=self._future_periods,
            ops_time_unit=self._ops_time_unit,
            states=self.states,
        )
        self.wallet_manager = WalletManager(client=self.binance, states=self.states)
        self.streams_manager = StreamsManager(
            binance=self.binance, states=self.states, test=self._test_net
        )
        self.decisions_manager = DecisionsManager(states=self.states)
        self.orders_manager = OrdersManager(binance=self.binance, states=self.states)
        logger.info("Start-up complete.")

    def _drop_old_entries(self):
        logger.info("Cleaning up old entries from dataframes...")
        self.states["trades"] = self.states["trades"][-2000:].reset_index(drop=True)
        self.states["pred_results"] = self.states["pred_results"][-2000:].reset_index(
            drop=True
        )
        self.states["pred_errors"] = self.states["pred_errors"].dropna()
        self.states["messages"] = self.states["messages"][-2000:]

    def _get_old_periods(self):
        return self._ops_frequency * 4

    def run(self):
        self.streams_manager.refresh()
        logger.info("Streams initilization complete.")
        schedule.every(1).minutes.do(self.crunch_messages)
        schedule.every(self._ops_frequency).minutes.do(self.execution_cycle)
        schedule.every(10).minutes.do(self.streams_manager.refresh)
        schedule.every(self._get_old_periods()).minutes.do(self._drop_old_entries)
        while not self._should_terminate:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        logger.info("Shutting down BitSurfer (TM)")
        self.streams_manager.stop()
        self._should_terminate = True

    def execution_cycle(self):
        logger.info("Running execution cycle...")
        self.predictions_manager.run_prediction()
        decision = self.decisions_manager.decide()
        if not decision:
            logger.info("Doin nothin.")
        else:
            logger.info(f"Decision: {decision}")
            self.orders_manager.test_order(decision)

    def crunch_messages(self):
        buffer_df = pd.DataFrame(columns=["ts", "price", "vol", "pair"])
        crunch = self.states["messages"][:]
        logger.info(f"Crunching {len(crunch)} messages.")
        for i, m in enumerate(crunch):
            try:
                ts = float(floor(m["E"] / 1000))
                price = float(m["p"])
                vol = float(m["q"])
                pair = m["s"]
                buffer_df.loc[i] = [ts, price, vol, pair]
            except KeyError as e:
                logger.error(f"Key error for message {m}")
        self.states["messages"] = [
            m for m in self.states["messages"] if m not in crunch
        ]
        for pair in buffer_df.pair.unique():
            pair_df = buffer_df[buffer_df["pair"] == pair].drop(columns="pair")
            pair_df["datetime"] = pd.to_datetime(pair_df["ts"], unit="s")
            pair_df = pair_df.set_index("datetime")
            pair_df = pair_df.resample("1T").mean()
            pair_df["pair"] = pair
            self.states["trades"] = (
                self.states["trades"].append(pair_df).reset_index(drop=True)
            )


if __name__ == "__main__":
    b = Bitsurfer()
    b.start()
