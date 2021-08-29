"""
MIT License
Copyright (c) 2021 vcokltfre
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from asyncio import Task, sleep
from sys import platform
from time import time

from aiohttp import WSMessage, WSMsgType

import ablaze
from ablaze.internal.http.resources import gateway

from .constants import GatewayCloseCodes as CloseCodes
from .constants import GatewayOps
from .ratelimiter import Ratelimiter


class Shard:
    def __init__(self, id: int, parent: "ablaze.GatewayClient") -> None:
        """A single gateway shard to receive and send events.

        :param id: The shard's ID.
        :type id: int
        :param parent: The shard's parent gateway client.
        :type parent: ablaze.GatewayClient
        :param loop: The even loop to use.
        :type loop: AbstractEventLoop
        """

        self.id = id
        self._parent = parent
        self._loop = parent._loop

        self._url = None
        self._ws = None

        self._session = None
        self._seq = None
        self._ws_seq = None

        self._heartbeat_task = None
        self._last_heartbeat_send = None
        self._recieved_ack = True
        self.latency = None

        self._pacemaker: Task = None

        self._send_limiter = Ratelimiter(120, 60, self._loop)

    def __repr__(self) -> str:
        return f"<Shard id={self.id} seq={self._seq}>"

    async def spawn_ws(self) -> None:
        """Spawn the websocket connection to the gateway."""

        self._ws = await self._parent._http.spawn_ws(self._url)

    async def connect(self) -> None:
        """Create a connection to the Discord gateway."""

        if not self._url:
            self._url = (await gateway.get_gateway(self._parent._http))["url"]

        while True:
            await self.spawn_ws()

            if self._session:
                await self.resume()

            await self.start_reader()

    async def close(self) -> None:
        """Gracefully close the connection."""

        self.failed_heartbeats = 0

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._pacemaker and not self._pacemaker.cancelled():
            self._pacemaker.cancel()

    async def send(self, data: dict) -> None:
        """Send data to the gateway.
        Args:
            data (dict): The data to send.
        """

        await self._send_limiter.wait()

        self._loop.create_task(self._parent.dispatch(self, "outbound", data))
        try:
            await self._ws.send_json(data)
        except ConnectionResetError:
            exit(1)

    async def identify(self) -> None:
        """Sends an identfy payload to the gateway."""

        await self.send(
            {
                "op": GatewayOps.IDENTIFY,
                "d": {
                    "token": self._parent._http._token,
                    "properties": {
                        "$os": platform,
                        "$browser": "Ablaze",
                        "$device": "Ablaze",
                    },
                    "intents": self._parent._intents,
                    "shard": [self.id, self._parent._shard_count],
                },
            }
        )

    async def resume(self) -> None:
        """Resume an existing connection with the gateway."""

        await self.send(
            {
                "op": GatewayOps.RESUME,
                "d": {
                    "token": self._parent.http.token,
                    "session_id": self._session,
                    "seq": self._seq,
                },
            }
        )

    async def heartbeat(self) -> None:
        """Send a heartbeat to the gateway."""

        self._last_heartbeat_send = time()

        await self.send({"op": GatewayOps.HEARTBEAT, "d": self._seq})

        if self._seq:
            self._seq += 1
        else:
            self._seq = 1

    async def dispatch(self, data: dict) -> None:
        """Dispatch events."""

        await self._parent.dispatch(self, "inbound", data)

        op = data["op"]

        if op == GatewayOps.HELLO:
            self._pacemaker = self._loop.create_task(
                self.start_pacemaker(data["d"]["heartbeat_interval"])
            )
            await self.identify()
        elif op == GatewayOps.ACK:
            self.latency = time() - self._last_heartbeat_send
            self._recieved_ack = True
        elif op == GatewayOps.RECONNECT:
            await self.close()
            await self.connect()

    async def handle_disconnect(self, code: int) -> None:
        """Handle the gateway disconnecting correctly."""

        if code in [
            CloseCodes.NOT_AUTHENTICATED,
            CloseCodes.AUTHENTICATION_FAILED,
            CloseCodes.INVALID_API_VERSION,
            CloseCodes.INVALID_INTENTS,
            CloseCodes.DISALLOWED_INTENTS,
        ]:
            await self._parent.panic(code)

        if code in [
            CloseCodes.INVALID_SEQ,
            CloseCodes.RATE_LIMITED,
            CloseCodes.SESSION_TIMEOUT,
        ]:
            self._session = None

            if code == CloseCodes.RATE_LIMITED:
                self._url = None

        self._seq = None

        await self.close()
        await self.connect()

    async def start_reader(self) -> None:
        """Start a loop constantly reading from the gateway."""

        async for message in self._ws:
            message: WSMessage

            if message.type == WSMsgType.TEXT:
                message_data = message.json()

                if s := message_data.get("s"):
                    self._ws_seq = s

                await self.dispatch(message_data)

        await self.handle_disconnect(self._ws.close_code)

    async def start_pacemaker(self, delay: float) -> None:
        """A loop to constantly heartbeat at an interval given by the gateway."""

        delay = delay / 1000

        while True:
            if not self._recieved_ack:
                return await self.close()

            await self.heartbeat()
            self._recieved_ack = False

            await sleep(delay)
