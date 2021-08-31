from asyncio import get_event_loop, sleep
from collections import defaultdict
from typing import Coroutine

import ablaze
from ablaze.internal.http.resources import gateway

from .ratelimiter import Ratelimiter
from .shard import Shard


class GatewayClient:
    def __init__(
        self,
        http: "ablaze.RESTClient",
        intents: int,
        shard_ids: list = None,
        shard_count: int = None,
    ) -> None:
        """A client to connect to the Discord gateway.

        :param http: The HTTP client to use for REST requests.
        :type http: ablaze.RESTClient
        :param intents: The gateway intents to connect with.
        :type intents: int
        :param shard_ids: The shard IDs to use, defaults to None
        :type shard_ids: list, optional
        :param shard_count: The number of shards to use, defaults to None
        :type shard_count: int, optional
        """

        self._http = http
        self._intents = intents

        self._shard_count = shard_count or 1
        self._shard_ids = shard_ids or list(range(self._shard_count))

        self._loop = get_event_loop()

        self.shards = [Shard(id, self) for id in self._shard_ids]

        self._listeners = defaultdict(list)

    def add_listener(self, event: str, listener: Coroutine) -> None:
        self._listeners[event.upper()].append(listener)

    async def panic(self, code) -> None:
        raise SystemExit(f"Shard error code: {code}")

    async def start(self) -> None:
        gw = await gateway.get_gateway_bot(self._http)
        limit = gw["session_start_limit"]

        limiter = Ratelimiter(limit["max_concurrency"], 5)

        if not self.shards:
            self.shards = [Shard(id, self) for id in range(gw["shards"])]

        for shard in self.shards:
            await limiter.wait()
            self._loop.create_task(shard.connect())

        while True:
            await sleep(0.1)

    async def dispatch(self, shard: Shard, direction: str, event: dict) -> None:
        name = event.get("t") or f"OP_{event['op']}"

        all_listeners = [
            *self._listeners[name],
            *(
                self._listeners["GATEWAY_SEND"]
                if direction == "outbound"
                else self._listeners["GATEWAY_RECEIVE"]
            ),
            *self._listeners["*"],
        ]

        for listener in all_listeners:
            self._loop.create_task(listener(shard, event))
