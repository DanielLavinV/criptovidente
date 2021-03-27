

class DecisionsManager:
    def __init__(self, balances, pairs_df, predictions_df):
        self._balances = balances
        self._pairs_df = pairs_df
        self._predictions_df = predictions_df

    def decide(self):
        decision = []
        current_asset = self.current_working_asset()
        if current_asset: # I have an asset currently
            logger.info(f"Determining what to do with {current_asset} holdings...")
            change = self.determine_change(current_asset)
            if change == "increase":
                logger.info("Current asset is good! Will hold it for another period.")
            elif change == "decrease" or change == "no_change":
                logger.info("Current asset bound to decrease/nochange. Will sell.")
                decision.append(("sell", current_asset))
                next_best = self.find_next_best(current_asset)
                if not next_best:
                    logger.warning("Unable to find next best asset! Doing nothing!")
                else:
                    logger.info(f"Found next best asset {next_best}. Will buy.")
                    decision.append(("buy", next_best))
        else: # I just have bitcoin
            logger.info("I only have bitcoin.")
            next_best = self.find_next_best("ninguna_moneda")
                if not next_best:
                    logger.warning("Unable to find promising asset! Doing nothing!")
                else:
                    logger.info(f"Found promising asset {next_best}. Will buy.")
                    decision.append(("buy", next_best))
        logger.info(f"DECIDED TO: {'do nothing' if not decision else decision}")
        return decision
            
    def find_next_best(self, current_asset):
        for i, row in self._pairs_df.sort_values(by="growth", ascending=False).iterrows():
            if current_asset in row["pair"]:
                continue
            prediction = self._predictions_df[row["pair"] == self._predictions_df["pair"]]
            if prediction.empty:
                continue
            if prediction["represents"] == "increase":
                return row["pair"].replace("btc", "")
        return None


    def current_working_asset(self):
        logger.info(f"Current assets: {self._balances.keys()}")
        for asset in self._balances.keys(): # wallet manager ensures only balances != 0 present
            if asset != "btc":
                return asset
        return None

    def determine_change(self, current_asset: str):
        asset_row = self._predictions_df[current_asset in self._predictions_df["pair"]]
        return asset_row["represents"] # either "increase", "decrease", "no_change"
