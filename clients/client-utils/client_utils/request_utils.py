from typing import Any, Dict
from requests import Request, Response


def forge_query_string(params: Dict[str, Any] = None) -> str:
    if not params:
        return ""
    querystr = f"?{list(params.keys())[0]}={list(params.values())[0]}"
    for key in list(params.keys())[1:]:
        if not params[key]:
            continue
        querystr += f"&{key}={params[key]}"
    return querystr


def forge_url(base: str, path: str, query_string: str = '') -> str:
    print(f"Reaching: {base + path + query_string}")
    return base + path + query_string


def add_request_headers(headers: Dict[str, Any], r: Request) -> Request:
    r.headers = headers
    return r


def response_to_dict(res: Response) -> dict:
    return {
        "http": res.status_code,
        "headers": dict(res.headers),
        "content": res.json()
    }
