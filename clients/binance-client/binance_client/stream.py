import asyncio
import websockets
import threading

# import orjson as json
import json
from typing import List, Callable, Any
from .constants import WEBSOCKET_BASE_ENDPOINT
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class BinanceStreamClient(threading.Thread):
    def __init__(
        self,
        streams: List[str],
        on_message: Callable[[Any], Any],
        how_many: str = "single",
    ):
        threading.Thread.__init__(self)
        self._how_many = how_many
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
            self.stop()

    def run(self):
        self._event_loop.run_until_complete(self.connect_and_subscribe())

    def _build_connection_string(self):
        logger.info(f"Subscribing to streams {self._streams}")
        if len(self._streams) == 1:
            con_string = f"{WEBSOCKET_BASE_ENDPOINT}/ws/{self._streams[0]}"
        else:
            con_string = (
                f"{WEBSOCKET_BASE_ENDPOINT}/stream?streams={'/'.join(self._streams)}"
            )
        return con_string

    def _build_subscription_string(self):
        return json.dumps({"method": "SUBSCRIBE", "params": self._streams, "id": 1})

    def stop(self):
        logger.info("Shutting down streams client...")
        self._should_terminate = True


# def something(msg):
#     print(msg)

# client = BinanceStreamClient(streams=["bnbbtc@trade"], on_message=something)
# client.start()
