# flake8: noqa
from client import BinanceClient
import signatures
import logging
import constants as c
import coins
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


client = BinanceClient("keys.json", False)
res1 = client.wallet.all_coins_information()
res2 = client.market_data.exchange_information()

with open("wololo.txt", "w+") as f:
    f.write(json.dumps(res1, indent=2))
    f.write("#" * 35)
    f.write("#" * 35)
    f.write(json.dumps(res2, indent=2))
# print(res["content"]["rateLimits"])
# client.wallet.system_status()
