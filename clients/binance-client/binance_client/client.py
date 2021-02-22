from requests import Request, Session, Response
import json
import constants
from datetime import datetime as dtt
import math
from signatures import sign
from endpoints import endpoints_config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BinanceClient:
    def __init__(self):
        with open("keys.json") as f:
            keys = json.load(f)
            self._api_key = keys["API_KEY"]
            self._secret_key = keys["SECRET_KEY"]
        self._session = Session()

    def get_system_status(self):
        req = self._forge_request("system_status", {})
        res = self._send(req)
        return res

    def dummy_request(self):
        pass

    def _forge_request(self, endpoint: str, params: dict) -> Request:
        cfg = endpoints_config[endpoint]
        url = self._forge_url(cfg)
        method = cfg["method"]
        security_headers, params = self._check_security(cfg, params)
        r = Request(method=method, url=url, params=params, headers=security_headers)
        return r

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
    
    def _send(self, req: Request) -> dict:
        logger.info(f"Reaching {req.url}")
        response = self._session.send(req.prepare())
        result = {
            "http_code": response.status_code,
            "content": response.json()
        }
        return result