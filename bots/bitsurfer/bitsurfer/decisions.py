import logging
from datetime import datetime as dtt
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DecisionsManager:
    def __init__(self, states):
        self.states = states

    def decide(self):
        decision = []
        current_asset = self.current_working_asset()
        if current_asset:  # I have an asset currently
            logger.info(f"Determining what to do with {current_asset} holdings...")
            change = self.determine_change(current_asset)
            if change is None:
                logger.info(
                    f"No prediction found for {current_asset}. Selling to avoid loss..."
                )
                decision.append(("SELL", current_asset + "BTC"))
            if change == "increase":
                logger.info("Current asset is good! Will hold it for another period.")
            elif change == "decrease" or change == "no_change":
                logger.info("Current asset bound to decrease/nochange. Will sell.")
                decision.append(("SELL", current_asset + "BTC"))
                next_best = self.find_next_best(current_asset)
                if not next_best:
                    logger.warning("Unable to find next best asset! Doing nothing!")
                else:
                    logger.info(f"Found next best asset {next_best}. Will buy.")
                    decision.append(("BUY", next_best))
        else:  # I just have bitcoin
            logger.info("I only have bitcoin.")
            next_best = self.find_next_best("ninguna_moneda")
            if not next_best:
                logger.warning("Unable to find promising asset! Doing nothing!")
            else:
                logger.info(f"Found promising asset {next_best}. Will buy.")
                decision.append(("BUY", next_best))
        logger.info(f"DECIDED TO: {'do nothing' if not decision else decision}")
        return decision

    def find_next_best(self, current_asset):
        logger.info(f"PREDICTIONS DF IN DECISIONS: \n{self.states['pred_results']}")
        for i, row in (
            self.states["pairs"].sort_values(by="growth", ascending=False).iterrows()
        ):
            if current_asset in row["pair"]:
                continue
            prediction = self.states["pred_results"][
                (row["pair"] == self.states["pred_results"]["pair"])
                & (
                    self.states["pred_results"]["ts"] > dtt.now().timestamp() + 5
                )  # just to make sure we select the most recent one
            ]
            if prediction.empty:
                logger.info(f"No prediction found for {row['pair']}")
                continue
            if prediction.shape[0] > 1:
                logger.info(
                    f"More than one prediction exists for {row['pair']} (now={dtt.now().timestamp()}). \
                    Skipping for decision...:\n {prediction.head(10)}"
                )
                continue
            logger.info(
                f"For {row['pair']} predicted a {prediction.reset_index()['represents'].iloc[0]} happening at {pd.to_datetime(prediction.reset_index()['ts'].iloc[0], unit='s')}"  # noqa: E501
            )
            if prediction.reset_index()["represents"].iloc[0] == "increase":
                return row["pair"]
        return None

    def current_working_asset(self):
        logger.info(f"Current assets: {self.states['balances'].keys()}")
        base_assets = ["BTC"]  # For real network
        for asset in self.states[
            "balances"
        ].keys():  # wallet manager ensures only balances != 0 present
            if asset not in base_assets:
                return asset
        return None

    def determine_change(self, current_asset: str):
        asset_row = self.states["pred_results"][
            self.states["pred_results"]["pair"].str.contains(current_asset)
        ]
        if asset_row.empty:
            return None
        return asset_row["represents"].iloc[
            0
        ]  # either "increase", "decrease", "no_change"
