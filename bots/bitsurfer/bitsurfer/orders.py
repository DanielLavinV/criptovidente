# noqa
import binance_client.constants as cts
from binance_client.coins import COIN_BTC
import logging
from time import sleep

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class OrdersManager:
    def __init__(self, binance, states):
        self.binance = binance
        self.states = states

    def create_orders(self, order_list):
        for i, order in enumerate(order_list):
            what, which = order
            if what == cts.ORDER_SIDE_BUY:
                r = self.binance.spot_account_trade.new_order(
                    symbol=which,
                    side=what,
                    order_type=cts.ORDER_TYPE_MARKET,
                    # I wish to spend all my bitcoin in this trade
                    quote_order_qty=self._current_asset_balance(COIN_BTC) / 50,
                )

            elif what == cts.ORDER_SIDE_SELL:
                r = self.binance.spot_account_trade.new_order(
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
                return
            client_order_id = r["content"]["clientOrderId"]
            success = self._ensure_order_completion(client_order_id, what, which)
            if not success:
                logger.warning(f"Cancelling order {client_order_id} for {which}")
                self.cancel_order(client_order_id, which)
                if len(order_list) == 2 and i == 0:
                    logger.warning(
                        f"Decision disrupted midway through, cannot do: {order_list[i+1]}"
                    )
                return

    def test_order(self, order_list):
        for order in order_list:
            what, which = order
            if what == cts.ORDER_SIDE_BUY:
                r = self.binance.spot_account_trade.test_new_order(
                    symbol=which,
                    side=what,
                    order_type=cts.ORDER_TYPE_MARKET,
                    # I wish to spend all my bitcoin in this trade
                    quote_order_qty=self._current_asset_balance(COIN_BTC) / 50,
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

    def cancel_order(self, client_order_id, which):
        r = self.binance.spot_account_trade.cancel_order(
            orig_client_order_id=client_order_id, symbol=which
        )
        if r["http_code"] != 200:
            self.cancel_order(client_order_id, which)
            return
        if r["content"]["status"] == "CANCELED":
            logger.info(f"Successfully cancelled orderID {client_order_id} for {which}")
        else:
            logger.error(f"Unable to cancel {client_order_id} for {which}")

    def _ensure_order_completion(self, client_order_id, what, which):
        order_complete = False
        max_retries = 50
        intento = 0
        sleep_time = 2
        while not order_complete:
            sleep(sleep_time)
            r = self.binance.spot_account_trade.query_order(
                symbol=which, orig_client_order_id=client_order_id
            )
            if r["http_code"] != 200:
                continue
            status = r["content"]["status"]
            if status == cts.ORDER_STATUS_FILLED:
                logger.info(f"Successful {what} of {which}. OrderID: {client_order_id}")
                order_complete = True
            else:
                if intento > max_retries:
                    logger.error(
                        f"Failed to {what} {which} after {sleep_time * max_retries} seconds. \
                             Cancelling order {client_order_id}"
                    )
                    return False
                else:
                    intento += 1
        return True

    def _current_asset_balance(self, asset):
        return self.states["balances"][asset.replace("BTC", "")]
