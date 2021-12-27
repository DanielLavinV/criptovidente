from .request_utils import *
from .signature_utils import *
import requests
import json

class BaseClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def get(self, path: str, headers: Dict[str, Any] = None, query_params: Dict[str,Any] = None) -> Dict:
        querystring = forge_query_string(query_params)
        url = forge_url(base=self._base_url, path=path, query_string=querystring)
        res = requests.get(
            url,
            headers=headers
        )
        return response_to_dict(res)

    def post(self, path: str, data: Dict, headers: Dict[str, Any] = None) -> Dict:
        url = forge_url(base=self._base_url, path=path)
        return requests.post(
            url,
            headers=headers,
            data=data
        )
