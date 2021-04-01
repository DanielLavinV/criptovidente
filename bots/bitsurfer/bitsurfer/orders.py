# noqa
import binance_client.constants as cts
from binance_client.coins import COIN_BTC
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class OrdersManager:
    def __init__(self, binance, states):
        self.binance = binance
        self.states = states

    def create_orders(self, order_list):
        for order in order_list:
            what, which = order

    def test_order(self, order_list):
        for order in order_list:
            what, which = order
            if what == cts.ORDER_SIDE_BUY:
                r = self.binance.spot_account_trade.test_new_order(
                    symbol=which,
                    side=what,
                    order_type=cts.ORDER_TYPE_MARKET,
                    # I wish to spend all my bitcoin in this trade
                    quote_order_qty=self._current_asset_balance(COIN_BTC),
                )

            elif what == cts.ORDER_SIDE_SELL:
                r = self.binance.spot_account_trade.test_new_order(
                    symbol=which,
                    side=what,
                    order_type=cts.ORDER_TYPE_MARKET,
                    # I wish to sell all of the asset
                    quantity=self._current_asset_balance(which),
                )
            if r["http_code"] == 200:
                logger.info("Correct order formation.")
            else:
                logger.error(
                    f"Received http error code: {r['http_code']} and {r['content']}"
                )

    def _ensure_order_completion(self):
        pass

    def _current_asset_balance(self, asset):
        return self.states["balances"][asset]
