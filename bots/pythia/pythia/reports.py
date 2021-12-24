import discord_notify as dn
from typing import List
import logging
from datetime import datetime as dtt
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

notifier = dn.Notifier(
    "https://discord.com/api/webhooks/829733851798437970/EIIAHfucMPrmOJ3x3uTBY1ofCKvMhVQYVcDD4-OznIAwcq4qvHOjmjvoT9PdldDhcDNS"  # noqa: E501
)


class ReportManager:
    def __init__(self, states):
        self.states = states

    def generate_report(self) -> List[str]:
        report = []
        report.append("#" * 40)
        report.append(
            f"LATEST REPORT: {pd.to_datetime(dtt.now().timestamp(), unit='s')}"
        )
        report.append("-" * 50)
        logger.info(self.states["pred_results"])
        for i, row in (
            self.states["pairs"].sort_values(by="growth", ascending=False).iterrows()
        ):
            prediction = self.states["pred_results"][
                (row["pair"] == self.states["pred_results"]["pair"])
                & (
                    self.states["pred_results"]["ts"] > (dtt.now().timestamp() + 10)
                )  # just to make sure we select the most recent one
            ]
            if prediction.empty:
                logger.error(f"No prediction found for {row['pair']}")
                continue
            if prediction.shape[0] > 1:
                logger.info(
                    f"More than one prediction exists for {row['pair']} (now={dtt.now().timestamp()}). \
                    Skipping for decision...:\n {prediction.head(10)}"
                )
                continue
            report.append(
                f"For {row['pair']} predicted a {prediction.reset_index()['represents'].iloc[0]} of {prediction.reset_index()['projection'].iloc[0]} happening at {pd.to_datetime(prediction.reset_index()['ts'].iloc[0], unit='s')}"  # noqa: E501
            )
        return report

    def report(self):
        report = self.generate_report()
        if len(report) == 0:
            return
        text = ""
        for row in report:
            text += row + "\n"
        notifier.send(text)
