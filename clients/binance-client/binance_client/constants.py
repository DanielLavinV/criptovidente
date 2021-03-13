BASE_ENDPOINT = "https://api.binance.com"
BASE_TEST_ENDPOINT = "https://testnet.binance.vision"
WEBSOCKET_BASE_ENDPOINT = "wss://stream.binance.com:9443"
FALLBACK_ENDPOINTS = [
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
]

KLINE_INTERVAL_MINUTES_1 = "1m"
KLINE_INTERVAL_MINUTES_3 = "3m"
KLINE_INTERVAL_MINUTES_5 = "5m"
KLINE_INTERVAL_MINUTES_15 = "15m"
KLINE_INTERVAL_MINUTES_30 = "30m"
KLINE_INTERVAL_HOURS_1 = "1h"
KLINE_INTERVAL_HOURS_2 = "2h"
KLINE_INTERVAL_HOURS_4 = "4h"
KLINE_INTERVAL_HOURS_6 = "6h"
KLINE_INTERVAL_HOURS_8 = "8h"
KLINE_INTERVAL_HOURS_12 = "12h"
KLINE_INTERVAL_DAYS_1 = "1d"
KLINE_INTERVAL_DAYS_3 = "3d"
KLINE_INTERVAL_WEEKS_1 = "1w"
KLINE_INTERVAL_MONTHS_1 = "1M"

RATE_LIMIT_TYPE_REQUEST_WEIGHT = "REQUEST_WEIGHT"
RATE_LIMIT_TYPE_ORDERS = "ORDERS"
RATE_LIMIT_TYPE_RAW_REQUESTS = "RAW_REQUESTS"

RATE_LIMIT_INTERVAL_SECOND = "SECOND"
RATE_LIMIT_INTERVAL_MINUTE = "MINUTE"
RATE_LIMIT_INTERVAL_DAY = "DAY"

CONTINGENCY_TYPE_OCO = "OCO"

FILTER_TYPE_PRICE_FILTER = "PRICE_FILTER"
FILTER_TYPE_PERCENT_PRICE = "PERCENT_PRICE"
FILTER_TYPE_LOT_SIZE = "LOT_SIZE"
FILTER_TYPE_MIN_NOTIONAL = "MIN_NOTIONAL"
FILTER_TYPE_ICEBERG_PARTS = "ICEBERG_PARTS"
FILTER_TYPE_MARKET_LOT_SIZE = "MARKET_LOT_SIZE"
FILTER_TYPE_MAX_NUM_ORDERS = "MAX_NUM_ORDERS"
FILTER_TYPE_MAX_NUM_ALGO_ORDERS = "MAX_NUM_ALGO_ORDERS"
FILTER_TYPE_MAX_NUM_ICEBERG_ORDERS = "MAX_NUM_ICEBERG_ORDERS"
FILTER_TYPE_MAX_POSITION_FILTER = "MAX_POSITION"
FILTER_TYPE_EXCHANGE_MAX_NUM_ORDERS = "EXCHANGE_MAX_NUM_ORDERS"
FILTER_TYPE_EXCHANGE_MAX_NUM_ALGO_ORDERS = "EXCHANGE_MAX_NUM_ALGO_ORDERS"


ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"
ORDER_STATUS_FILLED = "FILLED"
ORDER_STATUS_CANCELLED = "CANCELED"  # NOT A TYPO
ORDER_STATUS_PENDING_CANCEL = "PENDING_CANCEL"
ORDER_STATUS_REJECTED = "REJECTED"
ORDER_STATUS_EXPIRED = "EXPIRED"

ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_STOP_LOSS = "STOP_LOSS"
ORDER_TYPE_STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
ORDER_TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
ORDER_TYPE_LIMIT_MAKER = "LIMIT_MAKER"

ORDER_RESPONSE_TYPE_ACK = "ACK"
ORDER_RESPONSE_TYPE_RESULT = "RESULT"
ORDER_RESPONSE_TYPE_FULL = "FULL"

ORDER_SIDE_BUY = "BUY"
ORDER_SIDE_SELL = "SELL"

OCO_STATUS_EXECUTING = "EXECUTING"
OCO_STATUS_ALL_DONE = "ALL DONE"
OCO_STATUS_REJECT = "REJECT"

SYMBOL_STATUS_PRE_TRADING = "PRE_TRADING"
SYMBOL_STATUS_TRADING = "TRADING"
SYMBOL_STATUS_POST_TRADING = "POST_TRADING"
SYMBOL_STATUS_END_OF_DAY = "END_OF_DAY"
SYMBOL_STATUS_HALT = "HALT"
SYMBOL_STATUS_AUCTION_MATCH = "AUCTION_MATCH"
SYMBOL_STATUS_BREAK = "BREAK"

SYMBOL_TYPE_SPOT = "SPOT"

SNAPSHOT_TYPE_SPOT = "SPOT"
SNAPSHOT_TYPE_MARGIN = "MARGIN"
SNAPSHOT_TYPE_FUTURES = "FUTURES"

TIME_IN_FORCE_GOOD_TIL_CANCELLED = "GTC"
TIME_IN_FORCE_IMMEDIATE_OR_CANCEL = "IOC"
TIME_IN_FORCE_FILL_OR_KILL = "FOK"

HTTP_RESPONSE_CODES = {
    403: "WAF limit violated",
    418: "Banned after too many post-429 retries",
    429: "Request rate limit exceeded",
}

SECURITY_TYPE_NONE = "NONE"
SECURITY_TYPE_TRADE = "TRADE"
SECURITY_TYPE_MARGIN = "MARGIN"
SECURITY_TYPE_USER_DATA = "USER_DATA"
SECURITY_TYPE_USER_STREAM = "USER_STREAM"
SECURITY_TYPE_MARKET_DATA = "MARKET_DATA"

SECURITY_TYPES = {
    SECURITY_TYPE_NONE: {"requires_api_key": False, "requires_signature": False},
    SECURITY_TYPE_TRADE: {"requires_api_key": True, "requires_signature": True},
    SECURITY_TYPE_MARGIN: {"requires_api_key": True, "requires_signature": True},
    SECURITY_TYPE_USER_DATA: {"requires_api_key": True, "requires_signature": True},
    SECURITY_TYPE_USER_STREAM: {"requires_api_key": True, "requires_signature": False},
    SECURITY_TYPE_MARKET_DATA: {"requires_api_key": True, "requires_signature": False},
}
