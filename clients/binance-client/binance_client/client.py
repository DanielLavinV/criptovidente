from requests import Request
import json
import constants
from datetime import datetime as dtt
import math
from signatures import sign
from endpoints import endpoints_config

class BinanceClient:
    def __init__(self):
        with open("keys.json") as f:
            keys = json.load(f)
            self._api_key = keys["API_KEY"]
            self._secret_key = keys["SECRET_KEY"]

    def get_system_status(self):
        cfg = endpoints_config["system_status"]
        url = ""
        r = Request(cfg["method"], )

    def dummy_request(self):
        params = {"caca": "123", "cucu":"asdasd"}
        params = self._add_signature(params)
        r = Request("GET", constants.BASE_ENDPOINT, data=params)
        prep = r.prepare()
        # print(prep.body)

    def _add_signature(self, total_params: dict) -> dict:
        r = Request("", "http://ayy.lmao.com", data=total_params)
        prep = r.prepare()
        signature = sign(self._secret_key, prep.body)
        total_params["signature"] = signature
        return total_params

    def _timestamp(self) -> int:
        return int(math.floor(dtt.now().timestamp() * 1000))