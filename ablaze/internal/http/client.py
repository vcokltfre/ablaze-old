from asyncio import sleep
from collections import defaultdict
from logging import getLogger
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    overload,
)

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
from ..utils import _UNSET, UNSET
from .file import File
from .ratelimiting import RateLimitManager
from .route import Route

logger = getLogger("ablaze.http")

HTTPMethod = Literal["GET", "HEAD", "POST", "DELETE", "PUT", "PATCH"]
JSON = Union[str, float, int, Dict[str, "JSON"], List["JSON"], None]
ResponseFormat = Literal["bytes", "text", "json", "none"]


@overload
async def response_as(response: ClientResponse, format: Literal["bytes"]) -> bytes:
    ...


@overload
async def response_as(response: ClientResponse, format: Literal["text"]) -> str:
    ...


@overload
async def response_as(response: ClientResponse, format: Literal["json"]) -> JSON:
    ...


@overload
async def response_as(response: ClientResponse, format: Literal["none"]) -> None:
    ...


async def response_as(response: ClientResponse, format: ResponseFormat) -> Any:
    """Get the response as a specific format, and close the response."""

    if format == "bytes":
        data = await response.read()
    elif format == "text":
        data = await response.text()
    elif format == "json":
        data = await response.json()
    elif format == "none":
        data = None

    response.close()

    return data


class RESTClient:
    def __init__(self, token: str) -> None:
        """An HTTP client to make Discord API calls.

        :param token: The API token to use.
        :type token: str
        """

        self._token = token

        self._limiter = RateLimitManager()
        self._session: Optional[ClientSession] = None

        self._status: Mapping[int, Type[HTTPError]] = defaultdict(
            lambda: HTTPError,
            {
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
            },
        )

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

    @staticmethod
    def get_params(**params) -> dict:
        """Get a dictionary of query string or JSON parameters that are not UNSET.

        :return: The dictionary of query string or JSON parameters.
        :rtype: dict
        """

        return {k: v for k, v in params.items() if v is not UNSET}

    async def get(
        self,
        route: Route,
        files: Optional[Sequence[Union[File, _UNSET]]] = None,
        json: Union[JSON, _UNSET] = UNSET,
        reason: Optional[str] = None,
        qparams: Optional[dict] = None,
        format: ResponseFormat = "json",
    ) -> Any:
        return await self.request("GET", route, files, json, reason, qparams, format)

    async def post(
        self,
        route: Route,
        files: Optional[Sequence[Union[File, _UNSET]]] = None,
        json: Union[JSON, _UNSET] = UNSET,
        reason: Optional[str] = None,
        qparams: Optional[dict] = None,
        format: ResponseFormat = "json",
    ) -> Any:
        return await self.request("POST", route, files, json, reason, qparams, format)

    async def delete(
        self,
        route: Route,
        files: Optional[Sequence[Union[File, _UNSET]]] = None,
        json: Union[JSON, _UNSET] = UNSET,
        reason: Optional[str] = None,
        qparams: Optional[dict] = None,
        format: ResponseFormat = "json",
    ) -> Any:
        return await self.request("DELETE", route, files, json, reason, qparams, format)

    async def patch(
        self,
        route: Route,
        files: Optional[Sequence[Union[File, _UNSET]]] = None,
        json: Union[JSON, _UNSET] = UNSET,
        reason: Optional[str] = None,
        qparams: Optional[dict] = None,
        format: ResponseFormat = "json",
    ) -> Any:
        return await self.request("PATCH", route, files, json, reason, qparams, format)

    async def put(
        self,
        route: Route,
        files: Optional[Sequence[Union[File, _UNSET]]] = None,
        json: Union[JSON, _UNSET] = UNSET,
        reason: Optional[str] = None,
        qparams: Optional[dict] = None,
        format: ResponseFormat = "json",
    ) -> Any:
        return await self.request("PUT", route, files, json, reason, qparams, format)

    async def request(
        self,
        method: HTTPMethod,
        route: Route,
        files: Optional[Sequence[Union[File, _UNSET]]] = None,
        json: Union[JSON, _UNSET] = UNSET,
        reason: Optional[str] = None,
        qparams: Optional[dict] = None,
        format: ResponseFormat = "json",
    ) -> Any:
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
        :param qparams: The query parameters for the request, defaults to None
        :type qparams: dict, optional
        :param format: The format to return the response in, defaults to 'json'
        :type format: ResponseFormat, optional
        :return: The aiohttp ClientResponse of the request.
        :rtype: ClientResponse
        """

        headers = {}
        params = {}

        if qparams:
            params["params"] = qparams

        if reason:
            headers["X-Audit-Log-Reason"] = reason

        if files:
            files = [file for file in files if file is not UNSET]

        for attempt in range(3):
            if files:
                data = FormData()

                for file in files:
                    if not isinstance(file, File):
                        raise TypeError(
                            f"Files must be of type ablaze.File, not {file.__class__.__qualname__}"
                        )

                    if attempt:
                        file.reset()

                    data.add_field(
                        f"file_{file.filename}", file.file, filename=file.filename
                    )

                params["data"] = data
            elif json is not UNSET:
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
                    return await response_as(response, format)

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
                    raise self._status.get(status, self._status[0])(response)

                if attempt == 2:
                    raise self._status.get(status, self._status[0])(response)

                await sleep(sleep_for)

    async def spawn_ws(self, url: str):
        args = {
            "max_msg_size": 0,
            "timeout": 60,
            "autoclose": False,
            "headers": {"User-Agent": self._headers["User-Agent"]},
        }

        return await self.session.ws_connect(url, **args)
