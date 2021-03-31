# noqa
class OrdersManager:
    def __init__(self, binance):
        self.binance = binance

    def create_orders(self, order_list):
        for order in order_list:
            what, which = order
