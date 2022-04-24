from client_utils.client import BaseClient
from client_utils.signature_utils import sign_sha384
from typing import Any, Dict, Union, List
from .utils import *
import json
from .constants import *
from datetime import datetime as dtt
from math import floor


class PublicEndpoints:
    def __init__(self) -> None:
        self._client = BaseClient('https://api-pub.bitfinex.com')

    def platform_status(self) -> Dict:
        return self._client.get(
            path='/v2/platform/status',
        )

    def tickers(self, symbols: List[str] = ['tBTCUSD']) -> dict:
        res = self._client.get(
            path='/v2/tickers/',
            query_params={
                'symbols': ','.join(symbols)
            }
        )
        if res['http'] == 200:
            new_content = []
            for entry in res['content']:
                ticker_dict = ticker_symbol_list_to_dict(entry=entry[1:], symbol=entry[0])
                ticker_dict['symbol'] = entry[0]
                new_content.append(ticker_dict)
            res['content'] = new_content
        return res

    def ticker(self, symbol: str) -> dict:
        res = self._client.get(
            path=f'/v2/ticker/{symbol}'
        )
        if res['http'] == 200:
            res['content'] = ticker_symbol_list_to_dict(symbol, res['content'])
        return res

    def tickers_history(self, symbols: List[str], start: int = None, end: int = None, limit: int = None) -> dict:
        res = self._client.get(
            path='/v2/tickers/hist',
            query_params={
                'symbols': ','.join(symbols),
                'start': start,
                'end': end,
                'limit': limit
            }
        )
        if res['http'] == 200:
            res['content'] = [{
                'symbol': bymsol[0],
                'bid': bymsol[1],
                'ask': bymsol[3],
                'mts': bymsol[-1]
            } for bymsol in res['content']]
        return res

    def trades(self, symbol: str, limit: int = None, start: int = None, end: int = None, sort: int = None) -> dict:
        res = self._client.get(
            path=f'/v2/trades/{symbol}/hist',
            query_params={
                'limit': limit,
                'start': start,
                'end': end,
                'sort': sort
            }
        )
        if res['http'] == 200:
            res['content'] = [trades_symbol_list_to_dict(bymsol, symbol) for bymsol in res['content']]
        return res

    def book(self, symbol: str, precision: str, len: int = 1) -> dict:
        res = self._client.get(
            path=f'/v2/book/{symbol}/{precision}',
            query_params={
                'len': len
            }
        )
        if res['http'] == 200:
            res['content'] = [book_symbol_list_to_dict(symbol, entry, precision) for entry in res['content']]
        return res

    def stats(self, key: str, size: str, symbol: str, side: str, section: str, sort: int = None, start: int = None, end: int = None, limit: int = None) -> dict:
        side_path = f":{side}" if key == 'pos.size' else ""
        res = self._client.get(
            path=f'/v2/{key}:{size}:{symbol}{side_path}/{section}',
            query_params={
                'sort': sort,
                'start': start,
                'end': end,
                'limit': limit
            }
        )
        res['content'] = [{'mts': entry[0], 'value': entry[1]} for entry in res['content']]
        return res

    def candles(self, symbol: str, timeframe: str, section: str, period: str = None, sort: int = None, start: int = None, end: int = None, limit: int = None) -> dict:
        period_part = f':{period}' if period else ''
        res = self._client.get(
            path=f'/v2/candles/trade:{timeframe}:{symbol}{period_part}/{section}',
            query_params={
                'sort': sort,
                'start': start,
                'end': end,
                'limit': limit
            }
        )
        res['content'] = [candles_list_to_dict(res['content'])] if section == 'last' else [
            candles_list_to_dict(entry) for entry in res['content']]
        return res

    def configs(self, param_string: str) -> dict:
        """
        Access the configs enpoint.
        Parameters
        ---------
        param_string : str
            a string composed of Action:Object:Detail. Please refer to the official API documentation for valid permutations.
        """
        return self._client.get(
            path=f'/v2/conf/pub:{param_string}'
        )

    def derivatives_status(self, type: str, keys_string: str) -> dict:
        res = self._client.get(
            path=f'/v2/status/{type}',
            query_params={
                'keys': keys_string
            }
        )
        res['content'] = [{**{'key': entry[0]},
                           ** derivatives_status_list_to_dict(entry[1:])} for entry in res['content']]
        return res

    def derivatives_status_history(self, type: str, symbol: str, start: int = None, end: int = None, sort: int = None, limit: int = None) -> dict:
        res = self._client.get(
            path=f'/v2/status/{type}/{symbol}/hist',
            query_params={
                'sort': sort,
                'start': start,
                'end': end,
                'limit': limit
            }
        )
        res['content'] = [derivatives_status_list_to_dict(entry) for entry in res['content']]
        return res

    def liquidations(self, limit: int = None, start: int = None, end: int = None, sort: int = None) -> dict:
        res = self._client.get(
            path='/v2/liquidations/hist',
            query_params={
                'sort': sort,
                'start': start,
                'end': end,
                'limit': limit
            }
        )
        res['content'] = [liquidations_list_to_dict(entry) for entry in res['content'][0]]
        return res

    def leaderboards(self, key: str, time_frame: str, symbol: str, section: str, start: int = None, end: int = None, sort: int = None, limit: int = None) -> dict:
        res = self._client.get(
            path=f'/v2/rankings/{key}:{time_frame}:{symbol}/{section}',
            query_params={
                'sort': sort,
                'start': start,
                'end': end,
                'limit': limit
            }
        )
        res['content'] = [leaderboard_list_to_dict(entry) for entry in res['content']]
        return res

    def pulse_history(self):
        raise Exception("Method not yet implemented.")

    def pulse_profile_details(self):
        raise Exception("Method not yet implemented.")

    def funding_stats(self):
        raise Exception("Method not yet implemented.")


class PrivateEndpoints:
    def __init__(self, client_id: str = None, client_secret: str = None) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = BaseClient('https://api-pub.bitfinex.com')

    def _signed_post(self, path: str, body: Dict = None, headers: Dict[str, Any] = {}):
        nonce = floor(dtt.now().timestamp() * 1000)
        signature = f'/api{path}{nonce}{json.dumps(body) if body else ""}'
        sig = sign_sha384(self._client_secret, signature)
        headers['bfx-nonce'] = str(nonce)
        headers['bfx-signature'] = sig
        headers['bfx-apikey'] = self._client_id
        return self._client.post(path=path, data=body, headers=headers)

    def wallets(self):
        res = self._signed_post(
            path='/v2/auth/r/wallets',
        )
        return res

    def retrieve_orders(self):
        pass

    def submit_order(self):
        pass

    def order_update(self):
        pass

    def cancel_order(self):
        pass

    def order_multiop(self):
        pass

    def cancel_order_multi(self):
        pass

    def orders_history(self):
        pass

    def order_trades(self):
        pass

    def trades(self):
        pass

    def ledgers(self):
        pass

    def margin_info(self):
        pass

    def retrieve_positions(self):
        pass

    def claim_position(self):
        pass

    def increase_position(self):
        pass

    def increase_position_info(self):
        pass

    def positions_history(self):
        pass

    def positions_snapshot(self):
        pass

    def positions_audit(self):
        pass

    def derivative_position_collateral(self):
        pass

    def derivative_position_collateral_limits(self):
        pass

    def active_funding_offers(self):
        pass

    def submit_funding_offer(self):
        pass

    def cancel_funding_offer(self):
        pass

    def cancel_all_funding_offers(self):
        pass

    def funding_close(self):
        pass

    def funding_autorenew(self):
        pass

    def keep_funding(self):
        pass

    def funding_offers_history(self):
        pass

    def funding_loans(self):
        pass

    def funding_loans_history(self):
        pass

    def funding_credits(self):
        pass

    def funding_credits_history(self):
        pass


class BitfinexRestClient:
    def __init__(self, client_id: str = None, client_secret: str = None) -> None:
        self.private = PrivateEndpoints(client_id, client_secret)
        self.public = PublicEndpoints()


client = BitfinexRestClient(client_id="YOu4zqcDaMtcy1Z02G5WocZBosirK4QQcshnGNotvxP",
                            client_secret="aImRGlQZk6F8m9kv7CrWkWKpkBmE8yGVLIcttgh8EG7")
print(client.private.wallets())
