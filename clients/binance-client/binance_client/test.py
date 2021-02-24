from client import BinanceClient
import signatures
import logging
import constants as c
import coins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


client = BinanceClient("keys.json")
# res = client.get_system_status()
# res = client.wallet.all_coins_information()
# res = client.get_daily_account_snapshot(snapshot_type=c.SNAPSHOT_TYPE_SPOT)
# res = client.post_withdraw(coin=coins.COIN_EUR, address="caca", amount=0.0001)
res = client.market_data.exchange_information()

symbols = res["content"]["symbols"]
with open("symbols.py", "w+") as f:
    for s in symbols:
        f.write(f'SYMBOL_{s["symbol"]}: \"{s["symbol"]}\"\n')
