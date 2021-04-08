import asyncio
import websockets
import threading

# import orjson as json
import json
from typing import List, Callable, Any
from .constants import WEBSOCKET_BASE_ENDPOINT, WEBSOCKET_BASE_TEST_ENDPOINT
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BinanceStreamClient(threading.Thread):
    def __init__(
        self,
        streams: List[str],
        on_message: Callable[[Any], Any],
        test_net: bool = False,
    ):
        threading.Thread.__init__(self)
        self._test_net = test_net
        self._streams = streams
        self._on_message = on_message
        self._should_terminate = False
        self._event_loop = asyncio.new_event_loop()

    async def connect_and_subscribe(self):
        async with websockets.connect(self._build_connection_string(), ssl=True) as ws:
            await ws.send(self._build_subscription_string())
            while not self._should_terminate:
                try:
                    something = await ws.recv()
                    self._on_message(something)
                except Exception as e:
                    logger.error(f"Error when subscribing to streams: {e}")
                    self._should_terminate = True
            await ws.send(self._build_unsubscription_string())
            self.stop()

    def run(self):
        self._event_loop.run_until_complete(self.connect_and_subscribe())

    def _build_connection_string(self):
        logger.info(f"Subscribing to streams {self._streams}")
        base = (
            WEBSOCKET_BASE_ENDPOINT
            if not self._test_net
            else WEBSOCKET_BASE_TEST_ENDPOINT
        )
        if len(self._streams) == 1:
            con_string = f"{base}/ws/{self._streams[0]}"
        else:
            con_string = f"{base}/stream?streams={'/'.join(self._streams)}"
        return con_string

    def _build_unsubscription_string(self):
        return json.dumps({"method": "UNSUBSCRIBE", "params": self._streams, "id": 1})

    def _build_subscription_string(self):
        return json.dumps({"method": "SUBSCRIBE", "params": self._streams, "id": 1})

    def stop(self):
        logger.info("Shutting down streams client...")
        self._should_terminate = True


def something(msg):
    print(msg)


# client = BinanceStreamClient(
#     streams=["bnbbtc@trade", "btcusdt@trade",
# "btcbusd@trade", "ltcbtc@trade", "trxbtc@trade",
# "xrpbtc@trade", "ethbtc@trade"],
#     on_message=something,
#     test_net=True
# )
# client.start()
