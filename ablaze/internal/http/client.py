from asyncio import sleep
from collections import defaultdict
from json import dumps
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
from attr import dataclass

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
from .ratelimiting import BucketLock, RateLimitManager
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


@dataclass
class _Request:
    method: HTTPMethod
    route: Route
    headers: Dict[str, str]
    params: Dict[str, Any]
    files: Sequence[File]
    json: Any


@dataclass
class _Response:
    raw: ClientResponse
    successful: bool


class RESTClient:
    def __init__(self, token: str) -> None:
        """An HTTP client to make Discord API calls.

        :param token: The API token to use.
        :type token: str
        """

        self._token = token

        self._limiter = RateLimitManager()
        self._session: Optional[ClientSession] = None

        self._status_to_error_type: Mapping[int, Type[HTTPError]] = defaultdict(
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
        :return: The response, formatted according to the `format` argument
        :rtype: Any
        """

        headers = {}
        params = {}

        if qparams:
            params["params"] = qparams

        if reason:
            headers["X-Audit-Log-Reason"] = reason

        if files is not None:
            files = [file for file in files if not isinstance(file, _UNSET)]

        ATTEMPT_COUNT = 3

        for attempt in range(ATTEMPT_COUNT):
            req = _Request(method, route, headers, params, files or (), json)
            resp = await self._attempt_request(req)

            if resp.successful:
                return await response_as(resp.raw, format)

            if attempt == ATTEMPT_COUNT - 1:
                raise self._status_to_error_type[resp.raw.status](resp.raw)

            await sleep(1 + attempt * 2)

    async def _attempt_request(self, req: _Request) -> _Response:
        if req.files:
            data = FormData()

            for file in req.files:
                if not isinstance(file, File):
                    raise TypeError(
                        f"Files must be of type ablaze.File, not {file.__class__.__qualname__}"
                    )
                file.reset()
                data.add_field(
                    f"file_{file.filename}", file.file, filename=file.filename
                )

            # HACK: this is only used by endpoints that send messages, revisit later for a more general solution
            if req.json is not UNSET:
                data.add_field(
                    "payload_json", dumps(req.json), content_type="application/json"
                )

            req.params["data"] = data
        elif req.json is not UNSET:
            req.params["json"] = req.json

        bucket = await self._limiter.get_lock(req.route.bucket)

        async with bucket:
            return await self._make_rate_limited_request(req, bucket)

    async def _make_rate_limited_request(
        self, req: _Request, bucket: BucketLock
    ) -> _Response:
        response = await self.session.request(
            req.method,
            req.route.url,
            headers=req.headers,
            **req.params,
        )

        status = response.status
        headers = response.headers

        rl_reset_after = float(headers.get("X-RateLimit-Reset-After", 0))
        rl_bucket_remaining = int(headers.get("X-RateLimit-Remaining", 1))

        if 200 <= status <= 300:
            if rl_bucket_remaining > 0:
                bucket.defer(rl_reset_after)
            return _Response(response, successful=True)
        elif status == 429:
            if not req.headers.get("Via"):
                pass  # TODO: cf ratelimited

            json = await response.json()

            is_global = json.get("global", False)
            retry_after = json["retry_after"]

            if is_global:
                self._limiter.clear_global(retry_after)
            else:
                bucket.defer(retry_after)
        else:
            raise self._status_to_error_type[status](response)

        return _Response(response, successful=False)

    async def spawn_ws(self, url: str):
        args = {
            "max_msg_size": 0,
            "timeout": 60,
            "autoclose": False,
            "headers": {"User-Agent": self._headers["User-Agent"]},
        }

        return await self.session.ws_connect(url, **args)
