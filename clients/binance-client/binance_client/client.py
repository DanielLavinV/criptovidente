from requests import Request, Session, Response
import json
import constants
from datetime import datetime as dtt
import math
from signatures import sign
from endpoints import endpoints_config
import logging
from typing import Optional
from abc import ABC


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BaseClient:
    def __init__(self, keys_file: str):
        with open(keys_file) as f:
            keys = json.load(f)
            self._api_key = keys["API_KEY"]
            self._secret_key = keys["SECRET_KEY"]
        self._session = Session()

    def _forge_request_and_send(self, endpoint: str, params: dict) -> Request:
        cfg = endpoints_config[endpoint]
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
        result = {
            "http_code": response.status_code,
            "content": response.json()
        }
        return result


class WalletClient(BaseClient):
    def __init__(self, keys_file):
        super().__init__(keys_file)

    def system_status(self) -> dict:
        return self._forge_request_and_send("system_status", {})

    def all_coins_information(self, recv_window: int = 5000) -> dict:
        return self._forge_request_and_send("all_coins_information", {
            "recvWindow": recv_window,
            "timestamp": self._timestamp()
        })

    def daily_account_snapshot(
        self,
        snapshot_type: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000
    ) -> dict:
        limit = 5 if limit and limit < 5 else None
        limit = 30 if limit and limit > 30 else None
        params = {"type": snapshot_type, "recvWindow": recv_window, "timestamp": self._timestamp()}
        params = self._resolve_optional_arguments(
            params,
            startTime=start_time,
            endTime=end_time,
            limit=limit
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
        params = {"coin": coin, "address": address, "amount": amount, "recvWindow": recv_window, "timestamp": self._timestamp()}
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
        params = {"coin": coin, "address": address, "amount": amount, "recvWindow": recv_window, "timestamp": self._timestamp()}
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
        recv_window: int = 5000
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
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            asset=asset,
            status=status,
            startTime=start_time,
            endTime=end_time,
        )        
        return self._forge_request_and_send(endpoint="deposit_history_wapi", params=params)

    def withdraw_history_sapi(
        self,
        coin: Optional[str] = None,
        status: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000
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
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            asset=asset,
            status=status,
            startTime=start_time,
            endTime=end_time,
        )        
        return self._forge_request_and_send(endpoint="withdraw_history_wapi", params=params)

    def deposit_address_sapi(
        self,
        coin: str,
        network: Optional[str] = None,
        recv_window: int = 5000
    ) -> dict:
        params = {"coin": coin, "timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            network=network
        )
        return self._forge_request_and_send(endpoint="deposit_address_sapi", params=params)

    def deposit_address_wapi(
        self,
        asset: str,
        status: Optional[bool] = None,
        recv_window: int = 5000
    ) -> dict:
        params = {"asset": asset, "timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            status=status
        )
        return self._forge_request_and_send(endpoint="deposit_address_wapi", params=params)

    def account_status(
        self,
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        return self._forge_request_and_send(endpoint="account_status", params=params)

    def account_api_trading_status(
        self,
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        return self._forge_request_and_send(endpoint="account_api_trading_status", params=params)

    def dustlog(
        self,
        recv_window: int = 5000
    ):
        logger.info("Endpoint is not implemented.")

    def dust_transfer(
        self,
        asset: List[str],
        recv_window: int = 5000
    ):
        logger.info("Endpoint is not implemented.")

    def asset_dividend_record(
        self,
        asset: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            asset=asset,
            startTime=start_time,
            endTime=end_time,
            limit=limit
        )
        return self._forge_request_and_send(endpoint="asset_dividend_record", params=params)

    def asset_detail(
        self,
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        return self._forge_request_and_send(endpoint="asset_detail", params=params)

    def trade_fee(
        self,
        symbol: Optional[str] = None,
        recv_window: int = 5000
    ) -> dict:
        params = {"timestamp": self._timestamp(), "recvWindow": recv_window}
        params = self._resolve_optional_arguments(
            params,
            symbol=symbol
        )
        return self._forge_request_and_send(endpoint="trade_fee", params=params)

    def user_universal_transfer(
        self
    ):
        logger.info("Endpoint is not implemented.")

    def query_user_universal_transfer_history(
        self
    ):
        logger.info("Endpoint is not implemented.")

class BinanceClient(BaseClient):
    def __init__(self, keys_file):
        self.wallet = WalletClient(keys_file)
