from binance_client.client import BinanceClient
import pandas as pd
import threading
import time
import schedule
from predictions import PredictionsManager
from wallet import WalletManager
from streams import StreamsManager
from decisions import DecisionsManager
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
        self.binance = BinanceClient("/home/lavin/.binance/keys.json", False)
        self.binance_test = BinanceClient("/home/lavin/.binance/keys.json", True)
        self._ops_frequency = 1
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
        self._pairs = pd.DataFrame(columns=["pair", "growth"])
        self._messages = []
        self._max_pair_prices_vols = {}
        self._balances = {}
        self._should_terminate = False
        self.predictions_manager = PredictionsManager(
            messages=self._messages,
            pairs=self._pairs,
            ops_freq=self._ops_frequency,
            trades_df=self._trades_df,
            pred_results_df=self._prediction_results_df,
            pred_errors_df=self._prediction_errors_df,
            future_periods=self._future_periods,
            max_prices_vols=self._max_pair_prices_vols,
            ops_time_unit=self._ops_time_unit,
        )
        self.wallet_manager = WalletManager(
            client=self.binance, balances=self._balances
        )
        self.streams_manager = StreamsManager(
            pairs=self._pairs,
            binance=self.binance,
            max_pair_prices_vols=self._max_pair_prices_vols,
            messages=self._messages,
        )
        self.decisions_manager = DecisionsManager(
            balances=self._balances,
            pairs_df=self._pairs,
            predictions_df=self._prediction_results_df,
        )
        logger.info("Start-up complete.")

    def _drop_old_entries(self):
        logger.info("Cleaning up old entries from dataframes...")
        self._trades_df = self._trades_df[-5000:].reset_index(drop=True)
        self._prediction_results_df = self._prediction_results_df[-5000:].reset_index(
            drop=True
        )
        self._prediction_errors_df = self._prediction_errors_df.dropna()
        self._messages = self._messages[-5000:]

    def _get_old_periods(self):
        return self._ops_frequency * 10

    def run(self):
        # logger.info(f"Pairs in main before streams refresh: {self._pairs}")
        self.streams_manager.refresh()
        # logger.info(f"Pairs in main after streams refresh: {self._pairs}")
        logger.info("Streams initilization complete.")
        # schedule.every(self._ops_frequency).minutes.do(
        #     self.predictions_manager.run_prediction
        # )
        # This should be the final line
        schedule.every(self._ops_frequency).minutes.do(self.execution_cycle)
        schedule.every(30).minutes.do(self.streams_manager.refresh)
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
            # self.orders_manager.create(decision)


if __name__ == "__main__":
    b = Bitsurfer()
    b.start()
