from constants import SECURITY_TYPES, SECURITY_TYPE_MARKET_DATA, SECURITY_TYPE_NONE, SECURITY_TYPE_USER_DATA

endpoints_config = {

    "wallet": {
        "system_status": {
            "path": "/wapi/v3/systemStatus.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 0
        },
        "all_coins_information": {
            "path": "/sapi/v1/capital/config/getall",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "daily_account_snapshot": {
            "path": "/sapi/v1/accountSnapshot",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "disable_fast_withdraw_switch": {
            "path": "/sapi/v1/account/disableFastWithdrawSwitch",
            "method": "POST",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 0
        },
        "enable_fast_withdraw_switch": {
            "path": "/sapi/v1/account/enableFastWithdrawSwitch",
            "method": "POST",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 0
        },
        "withdraw_sapi": {
            "path": "/sapi/v1/capital/withdraw/apply",
            "method": "POST",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "withdraw_wapi": {
            "path": "/wapi/v3/withdraw.html",
            "method": "POST",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "deposit_history_sapi": {
            "path": "/sapi/v1/capital/deposit/hisrec",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "deposit_history_wapi": {
            "path": "/wapi/v3/depositHistory.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "withdraw_history_sapi": {
            "path": "/sapi/v1/capital/withdraw/history",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "withdraw_history_wapi": {
            "path": "/wapi/v3/withdrawHistory.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "deposit_address_sapi": {
            "path": "/sapi/v1/capital/deposit/address",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "deposit_address_wapi": {
            "path": "/wapi/v3/depositAddress.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "account_status": {
            "path": "/wapi/v3/accountStatus.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "account_api_trading_status": {
            "path": "/wapi/v3/apiTradingStatus.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "dustlog": {
            "path": "/wapi/v3/userAssetDribbletLog.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "dust_transfer": {},
        "asset_dividend_record": {
            "path": "/sapi/v1/asset/assetDividend",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "asset_detail": {
            "path": "/wapi/v3/assetDetail.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "trade_fee": {
            "path": "/wapi/v3/tradeFee.html",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_USER_DATA],
            "weight": 1
        },
        "user_universal_transfer": {},
        "query_user_universal_transfer_history": {},
    },
    
    "market_data": {
        "test_connectivity": {
            "path": "/api/v3/ping",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "check_server_time": {
            "path": "/api/v3/time",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "exchange_information": {
            "path": "/api/v3/exchangeInfo",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "order_book": {
            "path": "/api/v3/depth",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "recent_trades_list": {
            "path": "/api/v3/trades",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "old_trade_lookup": {
            "path": "/api/v3/historicalTrades",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_MARKET_DATA],
            "weight": 5
        },
        "compressed_aggregate_trades_list": {
            "path": "/api/v3/aggTrades",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "kline_candlestick_data": {
            "path": "/api/v3/klines",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "current_average_price": {
            "path": "/api/v3/avgPrice",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "twentyfourhour_ticker_price_change_statistics": {
            "path": "/api/v3/ticker/24hr",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "symbol_price_ticker": {
            "path": "/api/v3/ticker/price",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
        "symbol_order_book_ticker": {
            "path": "/api/v3/ticker/bookTicker",
            "method": "GET",
            "security": SECURITY_TYPES[SECURITY_TYPE_NONE],
            "weight": 1
        },
    }

}