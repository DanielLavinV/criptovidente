from typing import List
from .constants import *


def ticker_symbol_list_to_dict(symbol: str, entry: List) -> dict:
    d = {}
    if symbol[0] == 't':
        d['bid'] = entry[0]
        d['bid_size'] = entry[1]
        d['ask'] = entry[2]
        d['ask_size'] = entry[3]
        d['daily_change'] = entry[4]
        d['daily_change_relative'] = entry[5]
        d['last_price'] = entry[6]
        d['volume'] = entry[7]
        d['high'] = entry[8]
        d['low'] = entry[9]
    elif symbol[0] == 'f':
        d['frr'] = entry[0]
        d['bid'] = entry[1]
        d['bid_period'] = entry[2]
        d['bid_size'] = entry[3]
        d['ask'] = entry[4]
        d['ask_period'] = entry[5]
        d['ask_size'] = entry[6]
        d['daily_change'] = entry[7]
        d['daily_change_relative'] = entry[8]
        d['last_price'] = entry[9]
        d['volume'] = entry[10]
        d['high'] = entry[11]
        d['low'] = entry[12]
        d['_placeholder_1'] = entry[13]
        d['_placeholder_2'] = entry[14]
        d['frr_amount_available'] = entry[15]
    return d


def trades_symbol_list_to_dict(entry: List, symbol: str) -> dict:
    d = {}
    if symbol[0] == 't':
        d['id'] = entry[0]
        d['mts'] = entry[1]
        d['amount'] = entry[2]
        d['price'] = entry[3]
    elif symbol[0] == 'f':
        d['id'] = entry[0]
        d['mts'] = entry[1]
        d['amount'] = entry[2]
        d['rate'] = entry[3]
        d['period'] = entry[4]
    return d


def book_symbol_list_to_dict(symbol: str, entry: List, precision: str) -> dict:
    if symbol[0] == 't':
        if precision == BOOK_PRECISION_R0:
            return key_list_to_dict(['ORDER_ID', 'PRICE', 'AMOUNT'], entry)
        else:
            return key_list_to_dict(['price', 'count', 'amount'], entry)
    elif symbol[0] == 'f':
        if precision == BOOK_PRECISION_R0:
            return key_list_to_dict(['ORDER_ID', 'period', 'rate', 'amount'], entry)
        else:
            return key_list_to_dict(['rate', 'period', 'count', 'amount'], entry)


def candles_list_to_dict(entry: List) -> dict:
    return key_list_to_dict(["MTS", "OPEN", "CLOSE", "HIGH", "LOW", "VOLUME"], entry)


def derivatives_status_list_to_dict(entry: List) -> dict:
    return key_list_to_dict([
        "MTS",
        "PLACEHOLDER_0",
        "DERIV_PRICE",
        "SPOT_PRICE",
        "PLACEHOLDER_1",
        "INSURANCE_FUND_BALANCE",
        "PLACEHOLDER_2",
        "NEXT_FUNDING_EVT_TIMESTAMP_MS",
        "NEXT_FUNDING_ACCRUED",
        "NEXT_FUNDING_STEP",
        "PLACEHOLDER_3",
        "CURRENT_FUNDING",
        "PLACEHOLDER_4",
        "PLACEHOLDER_5",
        "MARK_PRICE",
        "PLACEHOLDER_6",
        "PLACEHOLDER_7",
        "OPEN_INTEREST",
        "PLACEHOLDER_8",
        "PLACEHOLDER_9",
        "PLACEHOLDER_10",
        "CLAMP_MIN",
        "CLAMP_MAX"
    ], entry)


def liquidations_list_to_dict(entry: List) -> dict:
    return key_list_to_dict([
        'pos',
        "POS_ID",
        "MTS",
        "PLACEHOLDER_0",
        "SYMBOL",
        "AMOUNT",
        "BASE_PRICE",
        "PLACEHOLDER_1",
        "IS_MATCH",
        "IS_MARKET_SOLD",
        "PLACEHOLDER_2",
        "PRICE_ACQUIRED"], entry)


def leaderboard_list_to_dict(entry: List) -> dict:
    return key_list_to_dict([
        "MTS",
        "PLACEHOLDER_0",
        "USERNAME",
        "RANKING",
        "PLACEHOLDER_1",
        "PLACEHOLDER_2",
        "VALUE",
        "PLACEHOLDER_3",
        "PLACEHOLDER_4",
        "TWITTER_HANDLE"
    ], entry)


def key_list_to_dict(key_list: List[str], entry: List) -> dict:
    d = {}
    for i, k in enumerate(key_list):
        d[k.lower()] = entry[i]
    return d
