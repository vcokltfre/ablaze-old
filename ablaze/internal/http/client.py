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

from asyncio import AbstractEventLoop, get_event_loop, sleep
from logging import getLogger
from typing import List, Literal, Union

from aiohttp import ClientResponse, ClientSession, FormData

from ...errors import (
    BadGateway,
    BadRequest,
    Forbidden,
    GatewayTimeout,
    HTTPError,
    MethodNotAllowed,
    NotFound,
    ServerError,
    ServiceUnavailable,
    TooManyRequests,
    Unauthorized,
    UnprocessableEntity,
)
from .file import File
from .ratelimiting import RateLimitManager
from .route import Route

logger = getLogger("ablaze.http")

HTTPMethod = Literal["GET", "HEAD", "POST", "DELETE", "PUT", "PATCH"]
JSON = Union[str, float, int, dict, list, bool]


class RESTClient:
    def __init__(self, token: str, *, loop: AbstractEventLoop = None) -> None:
        """An HTTP client to make Discord API calls.

        :param token: The API token to use.
        :type token: str
        :param loop: The event loop to use, defaults to None
        :type loop: AbstractEventLoop, optional
        """

        self._token = token
        self._loop = loop or get_event_loop()

        self._limiter = RateLimitManager(self._loop)
        self._session: ClientSession = None

        self._status = {
            400: BadRequest,
            401: Unauthorized,
            403: Forbidden,
            404: NotFound,
            405: MethodNotAllowed,
            422: UnprocessableEntity,
            429: TooManyRequests,
            500: ServerError,
            502: BadGateway,
            503: ServiceUnavailable,
            504: GatewayTimeout,
            "_": HTTPError,
        }

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bot {self._token}",
            "User-Agent": f"DiscordBot (Ablaze https://github.com/vcokltfre/ablaze)",
            "X-RateLimit-Precision": "milisecond",
        }

    @property
    def session(self) -> ClientSession:
        if self._session and not self._session.closed:
            return self._session
        self._session = ClientSession(headers=self._headers)
        return self._session

    async def request(
        self,
        method: HTTPMethod,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
    ) -> ClientResponse:
        """Make a request to the Discord API, following ratelimits.

        :param method: The HTTP method to use.
        :type method: HTTPMethod
        :param route: The route to request on.
        :type route: Route
        :param files: Files to upload, defaults to None
        :type files: List[File], optional
        :param json: JSON body for the request, defaults to None
        :type json: JSON, optional
        :param reason: The audit log reason for applicable actions, defaults to None
        :type reason: str, optional
        :return: The aiohttp ClientResponse of the request.
        :rtype: ClientResponse
        """

        headers = {}
        params = {}

        if reason:
            headers["X-Audit-Log-Reason"] = reason

        for attempt in range(3):
            if files:
                data = FormData()

                for file in files:
                    if attempt:
                        file.reset()

                    if not isinstance(file, File):
                        raise TypeError(
                            f"Files must be of type ablaze.File, not {file.__qualname__}"
                        )

                    data.add_field(
                        f"file_{file.filename}", file.file, filename=file.filename
                    )

                params["data"] = data
            elif json:
                params["json"] = json

            bucket = await self._limiter.get_lock(route.bucket)

            async with bucket:
                response = await self.session.request(
                    method,
                    route.url,
                    headers=headers,
                    **params,
                )

                status = response.status
                resp_headers = response.headers

                rl_reset_after = float(resp_headers.get("X-RateLimit-Reset-After", 0))
                rl_bucket_remaining = int(resp_headers.get("X-RateLimit-Remaining", 1))

                if status != 429 and rl_bucket_remaining:
                    bucket.defer(rl_reset_after)

                if 200 <= status <= 300:
                    return response

                sleep_for = 0

                if status == 429:
                    if not headers.get("Via"):
                        pass  # TODO: cf ratelimited

                    data = await response.json()

                    is_global = data.get("global", False)
                    retry_after = data["retry_after"]

                    if is_global:
                        self._limiter.clear_global(retry_after)
                    else:
                        bucket.defer(retry_after)

                elif status >= 500:
                    sleep_for = 1 + attempt * 2

                else:
                    raise self._status.get(status, self._status["_"])(response)

                if attempt == 2:
                    raise self._status.get(status, self._status["_"])(response)

                await sleep(sleep_for)

    async def spawn_ws(self, url: str):
        if not self.session or self.session.closed:
            self.session = ClientSession(headers=self.headers)

        args = {
            "max_msg_size": 0,
            "timeout": 60,
            "autoclose": False,
            "headers": {"User-Agent": self._headers["User-Agent"]},
        }

        return await self.session.ws_connect(url, **args)

    async def get_gateway(self) -> dict:
        route = Route("/gateway")

        return await (await self.request("GET", route)).json()

    async def get_gateway_bot(self) -> dict:
        route = Route("/gateway/bot")

        return await (await self.request("GET", route)).json()
