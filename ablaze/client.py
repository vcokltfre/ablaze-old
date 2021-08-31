from asyncio import get_event_loop
from asyncio.events import get_event_loop

from .internal import GatewayClient, RESTClient


class AblazeClient:
    def __init__(
        self, token: str, intents: int, shard_count: int = None, shard_ids: list = None
    ) -> None:
        self._loop = get_event_loop()

        self._http = RESTClient(token)
        self._gateway = GatewayClient(self._http, intents, shard_ids, shard_count)

    def run(self) -> None:
        """Make a blocking call to start the bot."""

        self._loop.run_until_complete(self._gateway.start())
        self._loop.run_forever()
