from constants import SECURITY_TYPES, SECURITY_TYPE_NONE, SECURITY_TYPE_USER_DATA

endpoints_config = {

    "system_status": {
        "path": "/wapi/v3/systemStatus",
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
        }
    },
}