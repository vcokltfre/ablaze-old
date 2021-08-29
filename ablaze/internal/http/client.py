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
from urllib.parse import quote
from warnings import warn

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
from ..utils import UNSET
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

    @staticmethod
    def _get_params(**params) -> dict:
        """Get a dictionary of query string or JSON parameters that are not UNSET.

        :return: The dictionary of query string or JSON parameters.
        :rtype: dict
        """

        return {k: v for k, v in params.items() if v is not UNSET}

    async def get(
        self,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
        qparams: dict = None,
    ):
        return await self.request("GET", route, files, json, reason, qparams)

    async def post(
        self,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
        qparams: dict = None,
    ):
        return await self.request("POST", route, files, json, reason, qparams)

    async def delete(
        self,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
        qparams: dict = None,
    ):
        return await self.request("DELETE", route, files, json, reason, qparams)

    async def patch(
        self,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
        qparams: dict = None,
    ):
        return await self.request("PATCH", route, files, json, reason, qparams)

    async def put(
        self,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
        qparams: dict = None,
    ):
        return await self.request("PUT", route, files, json, reason, qparams)

    async def request(
        self,
        method: HTTPMethod,
        route: Route,
        files: List[File] = None,
        json: JSON = None,
        reason: str = None,
        qparams: dict = None,
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
        :param qparams: The query parameters for the request, defaults to None
        :type qparams: dict, optional
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

        return await (await self.get(route)).json()

    async def get_gateway_bot(self) -> dict:
        route = Route("/gateway/bot")

        return await (await self.get(route)).json()

    async def get_guild_audit_log(
        self,
        guild_id: int,
        user_id: int = UNSET,
        action_type: int = UNSET,
        before: int = UNSET,
        limit: int = UNSET,
    ) -> dict:
        route = Route("/guilds/{guild_id}/audit-logs", guild_id=guild_id)
        params = self._get_params(
            user_id=user_id, action_type=action_type, before=before, limit=limit
        )

        return await (await self.get(route, qparams=params)).json()

    async def get_channel(self, channel_id: int) -> dict:
        route = Route("/channels/{channel_id}", channel_id=channel_id)

        return await (await self.get(route)).json()

    async def modify_guild_channel(
        self,
        channel_id: int,
        name: str = UNSET,
        type: int = UNSET,
        position: int = UNSET,
        topic: str = UNSET,
        nsfw: bool = UNSET,
        rate_limit_per_user: int = UNSET,
        bitrate: int = UNSET,
        user_limit: int = UNSET,
        permission_overwrites: list = UNSET,
        parent_id: int = UNSET,
        rtc_region: int = UNSET,
        video_quality_mode: int = UNSET,
        default_auto_archive_duration: int = UNSET,
        *,
        reason: str = None,
    ) -> dict:
        route = Route("/channels/{channel_id}", channel_id=channel_id)
        params = self._get_params(
            name=name,
            type=type,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            bitrate=bitrate,
            user_limit=user_limit,
            permission_overwrites=permission_overwrites,
            parent_id=parent_id,
            rtc_region=rtc_region,
            video_quality_mode=video_quality_mode,
            default_auto_archive_duration=default_auto_archive_duration,
        )

        return await (await self.patch(route, json=params, reason=reason)).json()

    async def modify_thread_channel(
        self,
        channel_id: int,
        name: str = UNSET,
        archived: bool = UNSET,
        auto_archive_duration: int = UNSET,
        locked: bool = UNSET,
        invitable: bool = UNSET,
        rate_limit_per_user: int = UNSET,
        *,
        reason: str = None,
    ) -> dict:
        route = Route("/channels/{channel_id}", channel_id=channel_id)
        params = self._get_params(
            name=name,
            archived=archived,
            auto_archive_duration=auto_archive_duration,
            locked=locked,
            invitable=invitable,
            rate_limit_per_user=rate_limit_per_user,
        )

        return await (await self.patch(route, json=params, reason=reason)).json()

    async def delete_channel(self, channel_id: int, *, reason: str = None) -> None:
        route = Route("/channels/{channel_id}", channel_id=channel_id)

        await self.delete(route, reason=reason)

    async def get_channel_messages(
        self,
        channel_id: int,
        around: int = UNSET,
        before: int = UNSET,
        after: int = UNSET,
        limit: int = UNSET,
    ) -> list:
        route = Route("/channels/{channel_id}/messages", channel_id=channel_id)
        params = self._get_params(
            around=around,
            before=before,
            after=after,
            limit=limit,
        )

        return await (await self.get(route, qparams=params)).json()

    async def get_channel_message(self, channel_id: int, message_id: int) -> dict:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}",
            channel_id=channel_id,
            message_id=message_id,
        )

        return await (await self.get(route)).json()

    async def create_message(
        self,
        channel_id: int,
        content: str = UNSET,
        tts: bool = UNSET,
        file: File = UNSET,
        embeds: list = UNSET,
        allowed_mentions: dict = UNSET,
        message_reference: dict = UNSET,
        components: list = UNSET,
        sticker_ids: list = UNSET,
    ) -> dict:
        route = Route("/channels/{channel_id}/messages", channel_id=channel_id)
        params = self._get_params(
            content=content,
            tts=tts,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
            message_reference=message_reference,
            components=components,
            sticker_ids=sticker_ids,
        )

        return await (await self.post(route, files=[file], json=params)).json()

    async def crosspost_message(self, channel_id: int, message_id: int) -> dict:
        route = Route("/channels/{channel_id}/messages/{message_id}/crosspost")

        return await (await self.post(route)).json()

    async def create_reaction(
        self, channel_id: int, message_id: int, emoji: str
    ) -> None:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id=channel_id,
            message_id=message_id,
            emoji=quote(emoji),
        )

        await self.put(route)

    async def delete_own_reaction(
        self, channel_id: int, message_id: int, emoji: str
    ) -> None:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id=channel_id,
            message_id=message_id,
            emoji=quote(emoji),
        )

        await self.delete(route)

    async def delete_user_reaction(
        self, channel_id: int, message_id: int, emoji: str, user_id: int
    ) -> None:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}",
            channel_id=channel_id,
            message_id=message_id,
            emoji=quote(emoji),
            user_id=user_id,
        )

        await self.delete(route)

    async def get_reactions(
        self,
        channel_id: int,
        message_id: int,
        emoji: str,
        after: int = UNSET,
        limit: int = UNSET,
    ) -> list:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id=channel_id,
            message_id=message_id,
            emoji=quote(emoji),
        )
        params = self._get_params(after=after, limit=limit)

        return await (await self.get(route, qparams=params)).json()

    async def delete_all_reactions(self, channel_id: int, message_id: int) -> None:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/reactions",
            channel_id=channel_id,
            message_id=message_id,
        )

        await self.delete(route)

    async def delete_all_reactions_for_emoji(
        self, channel_id: int, message_id: int, emoji: str
    ) -> None:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id=channel_id,
            message_id=message_id,
            emoji=quote(emoji),
        )

        await self.delete(route)

    async def edit_message(
        self,
        channel_id: int,
        message_id: int,
        content: str = UNSET,
        embeds: list = UNSET,
        flags: int = UNSET,
        file: File = UNSET,
        allowed_mentions: dict = UNSET,
        attachments: list = UNSET,
        components: list = UNSET,
    ) -> dict:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}",
            channel_id=channel_id,
            message_id=message_id,
        )
        params = self._get_params(
            content=content,
            embeds=embeds,
            flags=flags,
            allowed_mentions=allowed_mentions,
            attachments=attachments,
            components=components,
        )

        return await (await self.patch(route, files=[file], json=params)).json()

    async def delete_message(
        self, channel_id: int, message_id: int, *, reason: str = None
    ) -> None:
        route = Route("/channels/{channel_id}/messages/{message_id}")

        await self.delete(route, reason=reason)

    async def bulk_delete_messages(self, channel_id: int, messages: list) -> None:
        route = Route(
            "/channels/{channel_id}/messages/bulk-delete", channel_id=channel_id
        )
        params = self._get_params(
            messages=messages,
        )

        await self.delete(route, json=params)

    async def edit_channel_permissions(
        self,
        channel_id: int,
        overwrite_id: int,
        allow: str,
        deny: str,
        type: int,
        *,
        reason: str = None,
    ) -> None:
        route = Route(
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id=channel_id,
            overwrite_id=overwrite_id,
        )
        params = self._get_params(
            allow=allow,
            deny=deny,
            type=type,
        )

        await self.put(route, json=params, reason=reason)

    async def get_channel_invites(self, channel_id: int) -> list:
        route = Route("/channels/{channel_id}/invites")

        return await (await self.get(route)).json()

    async def create_channel_invite(
        self,
        channel_id: int,
        max_age: int = UNSET,
        max_uses: int = UNSET,
        temporary: bool = UNSET,
        unique: bool = UNSET,
        target_type: int = UNSET,
        target_user_id: int = UNSET,
        target_application_id: int = UNSET,
        *,
        reason: str = None,
    ) -> dict:
        route = Route("/channels/{channel_id}/invites", channel_id=channel_id)
        params = self._get_params(
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_type=target_type,
            target_user_id=target_user_id,
            target_application_id=target_application_id,
        )

        return await (await self.post(route, json=params, reason=reason)).json()

    async def delete_channel_permission(
        self, channel_id: int, overwrite_id: int, *, reason: str = None
    ) -> None:
        route = Route(
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id=channel_id,
            overwrite_id=overwrite_id,
        )

        await self.delete(route, reason=reason)

    async def follow_news_channel(
        self, channel_id: int, webhook_channel_id: int
    ) -> dict:
        route = Route("/channels/{channel_id}/followers", channel_id=channel_id)
        params = self._get_params(
            webhook_channel_id=webhook_channel_id,
        )

        return await (await self.post(route, json=params)).json()

    async def trigger_typing_indicator(self, channel_id: int) -> None:
        route = Route("/channels/{channel_id}/typing", channel_id=channel_id)

        await self.post(route)

    async def get_pinned_messages(self, channel_id: int) -> list:
        route = Route("/channels/{channel_id}/pins", channel_id=channel_id)

        return await (await self.get(route)).json()

    async def pin_message(
        self, channel_id: int, message_id: int, *, reason: str = None
    ) -> None:
        route = Route(
            "/channels/{channel_id}/pins/{message_id}",
            channel_id=channel_id,
            message_id=message_id,
        )

        await self.post(route, reason=reason)

    async def unpin_message(
        self, channel_id: int, message_id: int, *, reason: str = None
    ) -> None:
        route = Route(
            "/channels/{channel_id}/pins/{message_id}",
            channel_id=channel_id,
            message_id=message_id,
        )

        await self.delete(route, reason=reason)

    async def start_thread_with_message(
        self,
        channel_id: int,
        message_id: int,
        name: str,
        auto_archive_duration: int,
        *,
        reason: str = None,
    ) -> dict:
        route = Route(
            "/channels/{channel_id}/messages/{message_id}/threads",
            channel_id=channel_id,
            message_id=message_id,
        )
        params = self._get_params(
            name=name,
            auto_archive_duration=auto_archive_duration,
        )

        return await (await self.post(route, json=params, reason=reason)).json()

    async def start_thread_without_message(
        self,
        channel_id: int,
        name: str,
        auto_archive_duration: int,
        type: int = UNSET,
        invitable: bool = UNSET,
        *,
        reason: str = None,
    ) -> dict:
        route = Route("/channels/{channel_id}/threads")
        params = self._get_params(
            name=name,
            auto_archive_duration=auto_archive_duration,
            type=type,
            invitable=invitable,
        )

        await (await self.post(route, json=params, reason=reason)).json()

    async def join_thread(self, channel_id: int) -> None:
        route = Route(
            "/channels/{channel_id}/thread-members/@me", channel_id=channel_id
        )

        await self.put(route)

    async def add_thread_member(self, channel_id: int, user_id: int) -> None:
        route = Route(
            "/channels/{channel_id}/thread-members/{user_id}",
            channel_id=channel_id,
            user_id=user_id,
        )

        await self.put(route)

    async def leave_thread(self, channel_id: int) -> None:
        route = Route(
            "/channels/{channel_id}/thread-members/@me", channel_id=channel_id
        )

        await self.delete(route)

    async def remove_thread_member(self, channel_id: int, user_id: int) -> None:
        route = Route(
            "/channels/{channel_id}/thread-members/{user_id}",
            channel_id=channel_id,
            user_id=user_id,
        )

        await self.delete(route)

    async def list_thread_members(self, channel_id: int) -> None:
        route = Route("/channels/{channel_id}/thread-members", channel_id=channel_id)

        return await (await self.get(route)).json()

    async def list_active_threads(self, channel_id: int) -> None:
        warn(
            "list_active_threads() is a deprecated method and will be removed with the release of the v10 API."
        )
        route = Route("/channels/{channel_id}/threads/active", channel_id=channel_id)

        return await (await self.get(route)).json()

    async def list_public_archived_threads(
        self, channel_id: int, before: str = UNSET, limit: int = UNSET
    ) -> None:
        route = Route(
            "/channels/{channel_id}/threads/archived/public", channel_id=channel_id
        )
        params = self._get_params(
            before=before,
            limit=limit,
        )

        return await (await self.get(route, qparams=params)).json()

    async def list_private_archived_threads(
        self, channel_id: int, before: str = UNSET, limit: int = UNSET
    ) -> None:
        route = Route(
            "/channels/{channel_id}/threads/archived/private", channel_id=channel_id
        )
        params = self._get_params(
            before=before,
            limit=limit,
        )

        return await (await self.get(route, qparams=params)).json()

    async def list_joined_private_archived_threads(
        self, channel_id: int, before: str = UNSET, limit: int = UNSET
    ) -> None:
        route = Route(
            "/channels/{channel_id}/users/@me/threads/archived/private",
            channel_id=channel_id,
        )
        params = self._get_params(
            before=before,
            limit=limit,
        )

        return await (await self.get(route, qparams=params)).json()

    async def list_guild_emojis(self, guild_id: int) -> list:
        route = Route("/guilds/{guild_id}/emojis", guild_id=guild_id)

        return await (await self.get(route)).json()

    async def get_guild_emoji(self, guild_id: int, emoji_id: int) -> dict:
        route = Route("/guilds/{guild_id}/emojis/{emoji_id}", guild_id, emoji_id)

        return await (await self.get(route)).json()

    async def create_guild_emoji(
        self,
        guild_id: int,
        name: str,
        image: str,
        roles: list = [],
        *,
        reason: str = None,
    ) -> dict:
        route = Route("/guilds/{guild_id}/emojis", guild_id=guild_id)
        params = self._get_params(
            name=name,
            image=image,
            roles=roles,
        )

        return await (await self.post(route, json=params, reason=reason)).json()

    async def modify_guild_emoji(
        self,
        guild_id: int,
        emoji_id: int,
        name: str = UNSET,
        roles: list = UNSET,
        *,
        reason: str = None,
    ) -> dict:
        route = Route(
            "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id
        )
        params = self._get_params(
            name=name,
            roles=roles,
        )

        return await (await self.post(route, json=params, reason=reason)).json()

    async def delete_guild_emoji(
        self, guild_id: int, emoji_id: int, *, reason: str = None
    ) -> None:
        route = Route(
            "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id
        )

        await self.delete(route, reason=reason)
