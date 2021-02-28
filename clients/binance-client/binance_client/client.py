from requests import Request, Session, Response  # noqa: F401
import json
import constants
from datetime import datetime as dtt
import math
from signatures import sign
from endpoints import endpoints_config
import logging
from typing import Optional, List


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseClient:
    def __init__(self, keys_file: str, client_name: str):
        self.endpoints_config = endpoints_config[client_name]
        with open(keys_file) as f:
            keys = json.load(f)
            self._api_key = keys["API_KEY"]
            self._secret_key = keys["SECRET_KEY"]
        self._session = Session()

    def _forge_request_and_send(self, endpoint: str, params: dict) -> Request:
        cfg = self.endpoints_config[endpoint]
        url = self._forge_url(cfg)
        method = cfg["method"]
        security_headers, params = self._check_security(cfg, params)
        r = Request(method=method, url=url, params=params, headers=security_headers)
        return self._send(r)

    def _check_security(self, endpoint_config: dict, params: dict) -> dict:
        security_headers = {}
        security = endpoint_config["security"]
        if security["requires_api_key"]:
            security_headers["X-MBX-APIKEY"] = self._api_key
        if security["requires_signature"]:
            params = self._add_signature(params)
        return security_headers, params

    def _add_signature(self, total_params: dict) -> dict:
        r = Request("", "http://ayy.lmao.com", data=total_params)
        prep = r.prepare()
        signature = sign(self._secret_key, prep.body)
        total_params["signature"] = signature
        return total_params

    def _timestamp(self) -> int:
        return int(math.floor(dtt.now().timestamp() * 1000))

    def _forge_url(self, endpoint_config: dict) -> str:
        return constants.BASE_ENDPOINT + endpoint_config["path"]

    def _resolve_optional_arguments(self, params: dict, **kwargs) -> dict:
        for arg, val in kwargs.items():
            if val:
                params[arg] = val
        return params

    def _send(self, req: Request) -> dict:
        logger.info(f"Reaching {req.url}")
        response = self._session.send(req.prepare())
        result = {"http_code": response.status_code, "content": response.json()}
        return result


class WalletClient(BaseClient):
    def __init__(self, keys_file):
        super().__init__(keys_file, client_name="wallet")

    def system_status(self) -> dict:
        return self._forge_request_and_send("system_status", {})

    def all_coins_information(self, recv_window: int = 5000) -> dict:
        return self._forge_request_and_send(
            "all_coins_information",
            {"recvWindow": recv_window, "timestamp": self._timestamp()},
        )

    def daily_account_snapshot(
        self,
        snapshot_type: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000,
    ) -> dict:
        limit = 5 if limit and limit < 5 else None
        limit = 30 if limit and limit > 30 else None
        params = {
            "type": snapshot_type,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params, startTime=start_time, endTime=end_time, limit=limit
        )
        return self._forge_request_and_send("daily_account_snapshot", params=params)

    def disable_fast_withdraw_switch(self, recv_window: int = 5000):
        logger.info("Endpoint is not implemented")

    def enable_fast_withdraw_switch(self, recv_window: int = 5000):
        logger.info("Endpoint is not implemented")

    def withdraw_sapi(
        self,
        coin: str,
        address: str,
        amount: float,
        address_tag: Optional[str] = None,
        transaction_fee_flag: Optional[bool] = None,
        name: Optional[str] = None,
        withdraw_order_id: Optional[str] = None,
        network: Optional[str] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "coin": coin,
            "address": address,
            "amount": amount,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params,
            addressTag=address_tag,
            transactionFeeFlag=transaction_fee_flag,
            name=name,
            withdrawOrderId=withdraw_order_id,
            network=network,
        )
        return self._forge_request_and_send("withdraw_sapi", params=params)

    def withdraw_wapi(
        self,
        coin: str,
        address: str,
        amount: float,
        address_tag: Optional[str] = None,
        transaction_fee_flag: Optional[bool] = None,
        name: Optional[str] = None,
        withdraw_order_id: Optional[str] = None,
        network: Optional[str] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "coin": coin,
            "address": address,
            "amount": amount,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params,
            addressTag=address_tag,
            transactionFeeFlag=transaction_fee_flag,
            name=name,
            withdrawOrdeId=withdraw_order_id,
            network=network,
        )
        return self._forge_request_and_send("withdraw_wapi", params=params)

    def deposit_history_sapi(
        self,
        coin: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            coin=coin,
            status=status,
            startTime=start_time,
            endTime=end_time,
            offset=offset,
            limit=limit,
        )
        return self._forge_request_and_send("deposit_history_sapi", params=params)

    def deposit_history_wapi(
        self,
        asset: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params, asset=asset, status=status, startTime=start_time, endTime=end_time
        )
        return self._forge_request_and_send(
            endpoint="deposit_history_wapi", params=params
        )

    def withdraw_history_sapi(
        self,
        coin: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            coin=coin,
            status=status,
            startTime=start_time,
            endTime=end_time,
            offset=offset,
            limit=limit,
        )
        return self._forge_request_and_send("withdraw_history_sapi", params=params)

    def withdraw_history_wapi(
        self,
        asset: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params, asset=asset, status=status, startTime=start_time, endTime=end_time
        )
        return self._forge_request_and_send(
            endpoint="withdraw_history_wapi", params=params
        )

    def deposit_address_sapi(
        self, coin: str, network: Optional[str] = None, recv_window: int = 5000
    ) -> dict:
        params = {
            "coin": coin,
            "timestamp": self._timestamp(),
            "recvWindow": recv_window,
        }
        params = self._resolve_optional_arguments(params, network=network)
        return self._forge_request_and_send(
            endpoint="deposit_address_sapi", params=params
        )

    def deposit_address_wapi(
        self, asset: str, status: Optional[bool] = None, recv_window: int = 5000
    ) -> dict:
        params = {
            "asset": asset,
            "timestamp": self._timestamp(),
            "recvWindow": recv_window,
        }
        params = self._resolve_optional_arguments(params, status=status)
        return self._forge_request_and_send(
            endpoint="deposit_address_wapi", params=params
        )

    def account_status(self, recv_window: int = 5000) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        return self._forge_request_and_send(endpoint="account_status", params=params)

    def account_api_trading_status(self, recv_window: int = 5000) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        return self._forge_request_and_send(
            endpoint="account_api_trading_status", params=params
        )

    def dustlog(self, recv_window: int = 5000):
        logger.info("Endpoint is not implemented.")

    def dust_transfer(self, asset: List[str], recv_window: int = 5000):
        logger.info("Endpoint is not implemented.")

    def asset_dividend_record(
        self,
        asset: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params, asset=asset, startTime=start_time, endTime=end_time, limit=limit
        )
        return self._forge_request_and_send(
            endpoint="asset_dividend_record", params=params
        )

    def asset_detail(self, recv_window: int = 5000) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        return self._forge_request_and_send(endpoint="asset_detail", params=params)

    def trade_fee(self, symbol: Optional[str] = None, recv_window: int = 5000) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(params, symbol=symbol)
        return self._forge_request_and_send(endpoint="trade_fee", params=params)

    def user_universal_transfer(self):
        logger.info("Endpoint is not implemented.")

    def query_user_universal_transfer_history(self):
        logger.info("Endpoint is not implemented.")


class MarketDataClient(BaseClient):
    def __init__(self, keys_file):
        super().__init__(keys_file, "market_data")

    def test_connectivity(self) -> dict:
        return self._forge_request_and_send("test_connectivity", params={})

    def check_server_time(self) -> dict:
        return self._forge_request_and_send("check_server_time", params={})

    def exchange_information(self) -> dict:
        return self._forge_request_and_send("exchange_information", params={})

    def order_book(self, symbol: str, limit: Optional[int] = None) -> dict:
        params = {"symbol": symbol}
        params = self._resolve_optional_arguments(params, limit=limit)
        return self._forge_request_and_send("order_book", params)

    def recent_trades_list(self, symbol: str, limit: Optional[int] = None) -> dict:
        params = {"symbol": symbol}
        params = self._resolve_optional_arguments(params, limit=limit)
        return self._forge_request_and_send("recent_trades_list", params)

    def old_trade_lookup(
        self, symbol: str, limit: Optional[int] = None, from_id: Optional[int] = None
    ) -> dict:
        params = {"symbol": symbol}
        params = self._resolve_optional_arguments(params, limit=limit, fromId=from_id)
        return self._forge_request_and_send("old_trade_lookup", params)

    def compressed_aggregate_trades_list(
        self,
        symbol: str,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> dict:
        params = {"symbol": symbol}
        params = self._resolve_optional_arguments(
            params, limit=limit, fromId=from_id, startTime=start_time, endTime=end_time
        )
        return self._forge_request_and_send("compressed_aggregate_trades_list", params)

    def kline_candlestick_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int],
        end_time: Optional[int],
        limit: Optional[int],
    ) -> dict:
        params = {"symbol": symbol, "interval": interval}
        params = self._resolve_optional_arguments(
            params, limit=limit, startTime=start_time, endTime=end_time
        )
        return self._forge_request_and_send("kline_candlestick_data", params)

    def current_average_price(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        return self._forge_request_and_send("current_average_price", params)

    def twentyfourhour_ticker_price_change_statistics(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        return self._forge_request_and_send(
            "twentyfourhour_ticker_price_change_statistics", params
        )

    def symbol_price_ticker(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        return self._forge_request_and_send("symbol_price_ticker", params)

    def symbol_order_book_ticker(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        return self._forge_request_and_send("symbol_order_book_ticker", params)


class SpotAccountTradeClient(BaseClient):
    def __init__(self, keys_file):
        super().__init__(keys_file, "spot_account_trade")

    def test_new_order(
        self,
        symbol: str,
        side: List[str],
        order_type: List[str],
        time_in_force: Optional[List[int]] = None,
        quantity: Optional[float] = None,
        quote_order_qty: Optional[float] = None,
        price: Optional[float] = None,
        new_client_order_id: Optional[str] = None,
        stop_price: Optional[float] = None,
        iceberg_qty: Optional[float] = None,
        new_order_resp_type: List[str] = None,
        recv_window: float = 5000,
    ) -> dict:
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            timeInForce=time_in_force,
            quantity=quantity,
            quoteOrderQty=quote_order_qty,
            price=price,
            newClientOrderId=new_client_order_id,
            stopPrice=stop_price,
            icebergQty=iceberg_qty,
            newOrderRespType=new_order_resp_type,
        )
        return self._forge_request_and_send("test_new_order", params)

    def new_order(
        self,
        symbol: str,
        side: List[str],
        order_type: List[str],
        time_in_force: Optional[List[int]] = None,
        quantity: Optional[float] = None,
        quote_order_qty: Optional[float] = None,
        price: Optional[float] = None,
        new_client_order_id: Optional[str] = None,
        stop_price: Optional[float] = None,
        iceberg_qty: Optional[float] = None,
        new_order_resp_type: List[str] = None,
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params,
            timeInForce=time_in_force,
            quantity=quantity,
            quoteOrderQty=quote_order_qty,
            price=price,
            newClientOrderId=new_client_order_id,
            stopPrice=stop_price,
            icebergQty=iceberg_qty,
            newOrderRespType=new_order_resp_type,
        )
        return self._forge_request_and_send("new_order", params)

    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int],
        orig_client_order_id: Optional[str],
        new_client_order_id: Optional[str],
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "symbol": symbol,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params,
            orderId=order_id,
            origClientOrderId=orig_client_order_id,
            newClientOrderId=new_client_order_id,
        )
        return self._forge_request_and_send("cancel_order", params)

    def cancel_all_open_orders_on_symbol(
        self, symbol: str, recv_window: int = 5000
    ) -> dict:
        params = {
            "symbol": symbol,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        return self._forge_request_and_send("cancel_all_open_orders_on_symbol", params)

    def query_order(
        self,
        symbol: str,
        order_id: Optional[int],
        orig_client_order_id: Optional[str],
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "symbol": symbol,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params, orderId=order_id, origClientOrderId=orig_client_order_id
        )
        return self._forge_request_and_send("query_order", params)

    def current_open_orders(self, symbol: str, recv_window: int = 5000) -> dict:
        params = {
            "symbol": symbol,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        return self._forge_request_and_send("current_open_orders", params)

    def all_orders(
        self,
        symbol: str,
        order_id: Optional[int],
        start_time: Optional[int],
        end_time: Optional[int],
        limit: Optional[int],
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "symbol": symbol,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params,
            orderId=order_id,
            startTime=start_time,
            endTime=end_time,
            limit=limit,
        )
        return self._forge_request_and_send("all_orders", params)

    def new_oco(
        self,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        list_client_order_id: Optional[str],
        limit_client_order_id: Optional[str],
        limit_iceberg_qty: Optional[float],
        stop_client_order_id: Optional[str],
        stop_limit_price: Optional[float],
        stop_iceberg_qty: Optional[float],
        stop_limit_time_in_force: List[str],
        new_order_resp_type: List[str],
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
            "side": side,
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
        }
        params = self._resolve_optional_arguments(
            params,
            listClientOrderId=list_client_order_id,
            limitClientOrderId=limit_client_order_id,
            limitIcebergQty=limit_iceberg_qty,
            stopClientOrderId=stop_client_order_id,
            stopLimitPrice=stop_limit_price,
            stopIcebergQty=stop_iceberg_qty,
            stopLimitTimeInForce=stop_limit_time_in_force,
            newOrderRespType=new_order_resp_type,
        )
        return self._forge_request_and_send("new_oco", params)

    def cancel_oco(
        self,
        symbol: str,
        order_list_id: Optional[int],
        list_client_order_id: Optional[str],
        new_client_order_id: Optional[str],
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
            "symbol": symbol,
        }
        params = self._resolve_optional_arguments(
            params,
            orderListId=order_list_id,
            listClientOrderId=list_client_order_id,
            newClientOrderId=new_client_order_id,
        )
        return self._forge_request_and_send("cancel_oco", params)

    def query_oco(
        self,
        order_list_id: Optional[int],
        orig_client_order_id: Optional[str],
        recv_window: int = 5000,
    ) -> dict:
        params = {"recvWindow": recv_window, "timestamp": self._timestamp()}
        params = self._resolve_optional_arguments(
            params, orderListId=order_list_id, origClientOrderId=orig_client_order_id
        )
        return self._forge_request_and_send("query_oco", params)

    def query_all_oco(
        self,
        from_id: Optional[int],
        start_time: Optional[int],
        end_time: Optional[int],
        limit: Optional[int],
        recv_window: int = 5000,
    ) -> dict:
        params = {"recvWindow": recv_window, "timestamp": self._timestamp()}
        params = self._resolve_optional_arguments(
            params, fromId=from_id, starTime=start_time, endTime=end_time, limit=limit
        )
        return self._forge_request_and_send("query_all_oco", params)

    def query_open_oco(self, recv_window: int = 5000) -> dict:
        params = {"recvWindow": recv_window, "timestamp": self._timestamp()}
        return self._forge_request_and_send("query_open_oco", params)

    def account_information(self, recv_window: int = 5000) -> dict:
        params = {"recvWindow": recv_window, "timestamp": self._timestamp()}
        return self._forge_request_and_send("account_information", params)

    def account_trade_list(
        self,
        symbol: str,
        from_id: Optional[int],
        start_time: Optional[int],
        end_time: Optional[int],
        limit: Optional[int],
        recv_window: int = 5000,
    ) -> dict:
        params = {
            "symbol": symbol,
            "recvWindow": recv_window,
            "timestamp": self._timestamp(),
        }
        params = self._resolve_optional_arguments(
            params, fromId=from_id, starTime=start_time, endTime=end_time, limit=limit
        )
        return self._forge_request_and_send("account_trade_list", params)


class UserDataClient(BaseClient):
    def __init__(self, keys):
        super().__init__(keys, "user_data")

    def create_listen_key(self) -> dict:
        return self._forge_request_and_send("create_listen_key", params={})

    def ping_listen_key(self, listen_key: str) -> dict:
        params = {"listenKey": listen_key}
        return self._forge_request_and_send("ping_listen_key", params)

    def close_listen_key(self, listen_key: str) -> dict:
        params = {"listenKey": listen_key}
        return self._forge_request_and_send("close_listen_key", params)


class BinanceClient(BaseClient):
    def __init__(self, keys_file):
        self.wallet = WalletClient(keys_file)
        self.market_data = MarketDataClient(keys_file)
        self.spot_account_trade = SpotAccountTradeClient(keys_file)
        self.user_data = UserDataClient(keys_file)
