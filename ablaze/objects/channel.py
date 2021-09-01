import ablaze.objects.messages as messages
from ablaze.objects.utils import extract_int, nullmap
import asyncio
import warnings
from ablaze.objects.permissions import PermissionFlags
from datetime import datetime
from ablaze.objects.user import User
from enum import IntEnum
from typing import (
    Any, AsyncIterator, Awaitable, Callable, ContextManager, Dict,
    Iterable, Optional, Protocol, Sequence, Type, TypeVar, Union, overload
)
from ablaze.internal.utils import _UNSET, UNSET
from ablaze.internal.http.resources import channel as res
from ablaze.internal.http.client import RESTClient
from dataclasses import dataclass
from abc import ABC,  abstractmethod
from .abc import Snowflake


_T = TypeVar("_T")
_R = TypeVar("_R")
_C = TypeVar("_C", bound="Channel")
U = Union[_UNSET, _T]


def channel_from_json(state: "State", json: dict) -> "Channel":
    channel_type = _CHANNEL_TYPE_TO_CLASS[json["type"]]
    return channel_type.from_json(state, json)


### <Stubs>
# These are stubs for classes that are not yet implemented.


class Member(Snowflake):
    id: int


class Guild(Snowflake):
    id: int


class Cache(Protocol):
    def get_guild(self, id: int) -> Optional[Guild]: ...
    def get_channel(self, id: int) -> Optional["Channel"]: ...

### </Stub>


@dataclass(frozen=True)
class State:
    http: RESTClient
    cache: Cache


class AutoArchiveDuration(IntEnum):
    HOUR = 60
    ONE_DAY = 1440
    THREE_DAYS = 4320
    SEVEN_DAYS = 10080


class VideoQualityMode(IntEnum):
    AUTO = 1
    FULL = 2


class OverwriteType(IntEnum):
    ROLE = 0
    MEMBER = 1


@dataclass(frozen=True)
class PermissionOverwrite:
    id: int
    type: OverwriteType
    allow: PermissionFlags
    deny: PermissionFlags

    def to_json(self):
        return {
            "id": self.id,
            "type": self.type,
            "allow": self.allow,
            "deny": self.deny,
        }


@dataclass(frozen=True)
class Channel(ABC, Snowflake):
    id: int
    _state: State

    async def _delete(self, reason: Optional[str] = None):
        await res.delete_channel(self._state.http, self.id, reason=reason)

    @classmethod
    @abstractmethod
    def from_json(cls: Type[_C], state: State, json: dict) -> _C:
        ...


_MesssageRef = Union[Snowflake, int, None]


class _Typing:
    """
    Async context manager for a typing indicator.
    """
    def __init__(self, refresh: Callable[[], Awaitable[None]]):
        self.stopped = False
        self.refresh = refresh
        self._task = asyncio.create_task(self.sleep_forever())

    async def sleep_forever(self):
        while not self.stopped:
            await self.refresh()
            await asyncio.sleep(5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stopped = True

    def __del__(self):
        if not self.stopped:
            warnings.warn("You should use `channel.typing()` in a context manager (the `with` statement)")
            self.stopped = True


class TextChannel(Channel):
    messages_module = messages  # we have to do this because we have a method called `messages`

    @overload
    async def messages(self, *, limit: int = ..., around: _MesssageRef) -> Sequence[messages_module.Message]: ...
    @overload
    async def messages(self, *, limit: int = ..., before: _MesssageRef) -> Sequence[messages_module.Message]: ...
    @overload
    async def messages(self, *, limit: int = ..., after: _MesssageRef) -> Sequence[messages_module.Message]: ...
    @overload
    async def messages(self, *, limit: int = ...) -> Sequence[messages_module.Message]: ...

    async def messages(self, **kwargs) -> Sequence[messages_module.Message]:
        if len(kwargs.keys() & {"before", "after", "around"}) > 1:
            raise TypeError("Can provide at most one of {around, before, after}")

        kwargs = {k: extract_int(v) for k, v in kwargs.items() if v is not None}

        message_jsons = await res.get_channel_messages(
            self._state.http,
            channel_id=self.id,
            **kwargs
        )
        return [messages.Message.from_json(json) for json in message_jsons]

    async def bulk_delete(self, messages: Iterable[Union[Snowflake, int]]) -> None:
        await res.bulk_delete_messages(
            self._state.http,
            channel_id=self.id,
            messages=[extract_int(m) for m in messages]
        )

    def typing(self) -> ContextManager:
        async def refresh_typing():
            await res.trigger_typing_indicator(
                self._state.http,
                channel_id=self.id
            )
        return _Typing(refresh_typing)

    async def pinned_messages(self):
        message_jsons = await res.get_pinned_messages(
            self._state.http,
            channel_id=self.id,
        )
        return [messages.Message.from_json(m) for m in message_jsons]

    async def send(self, content: messages_module.BaseMessageContent) -> messages_module.Message:
        rendered = content.render()
        return messages.Message.from_json(await res.create_message(
            self._state.http,
            channel_id=self.id,
            file=rendered.file or UNSET,
            **rendered.json,
        ))


@dataclass(frozen=True)
class DMChannel(TextChannel):
    recipient: User

    async def close(self, *, reason: Optional[str] = None):
        await self._delete(reason=reason)

    @classmethod
    def from_json(cls, state: State, json: dict) -> "DMChannel":
        return DMChannel(
            id=int(json["id"]),
            _state=state,
            recipient=User.from_json(json["recipients"][0]),
        )


_GC = TypeVar("_GC", bound="GuildChannel")


@dataclass(frozen=True)
class GuildChannel(Channel):
    guild_id: int
    name: str

    async def set_permission_overwrite(
        self,
        overwrite: PermissionOverwrite,
        reason: Optional[str] = None
    ) -> None:
        overwrite_json = overwrite.to_json()
        overwrite_json["overwrite_id"] = overwrite_json.pop("id")
        await res.edit_channel_permissions(
            self._state.http,
            channel_id=self.id,
            reason=reason,
            **overwrite_json
        )

    async def delete_permission_overwrite(
        self,
        id: Union[Snowflake, int],
        reason: Optional[str] = None
    ) -> None:
        await res.delete_channel_permission(
            self._state.http,
            channel_id=self.id,
            overwrite_id=extract_int(id),
            reason=reason
        )

    # TODO: Invites

    async def delete(self, *, reason: Optional[str] = None):
        await self._delete(reason=reason)

    async def _edit(self, **kwargs: Any) -> dict:
        return await res.modify_guild_channel(
            self._state.http,
            channel_id=self.id,
            **kwargs
        )

    async def edit(
        self: _GC,
        *,
        name: U[str] = UNSET,
        position: U[int] = UNSET,
        permission_overwrites: U[Iterable[PermissionOverwrite]] = UNSET,
    ) -> _GC:
        return self.from_json(self._state, await self._edit(
            name=name,
            position=position,
            permission_overwrites=
                UNSET if isinstance(permission_overwrites, _UNSET)
                else [o.to_json() for o in permission_overwrites]
        ))


@dataclass(frozen=True)
class HasPosition(Channel):
    position: int


@dataclass(frozen=True)
class GuildTextChannel(TextChannel, GuildChannel, HasPosition):
    category_id: Optional[int]
    topic: Optional[str]
    slowmode_seconds: int

    async def start_public_thread(
        self,
        name: str,
        auto_archive_duration: AutoArchiveDuration = AutoArchiveDuration.ONE_DAY,
    ):
        await res.start_thread_without_message(
            self._state.http,
            channel_id=self.id,
            name=name,
            type=11,
            auto_archive_duration=auto_archive_duration
        )

    async def start_private_thread(
        self,
        name: str,
        auto_archive_duration: AutoArchiveDuration = AutoArchiveDuration.ONE_DAY,
    ):
        await res.start_thread_without_message(
            self._state.http,
            channel_id=self.id,
            name=name,
            type=12,
            auto_archive_duration=auto_archive_duration
        )

    async def edit(
        self,
        *,
        name: U[str] = UNSET,
        position: U[int] = UNSET,
        topic: U[Optional[str]] = UNSET,
        nsfw: U[bool] = UNSET,
        slowmode_seconds: U[int] = UNSET,
        category: U[Union["Category", int]] = UNSET,
        default_auto_archive_duration_minutes: U[int] = UNSET,
        permission_overwrites: U[Iterable[PermissionOverwrite]] = UNSET,
    ) -> "GuildTextChannel":
        if isinstance(category, Category):
            category = category.id

        return self.from_json(self._state, await self._edit(
            name=name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=slowmode_seconds,
            category=category,
            default_auto_archive_duration=default_auto_archive_duration_minutes,
            permission_overwrites=
                UNSET if isinstance(permission_overwrites, _UNSET)
                else [o.to_json() for o in permission_overwrites]
        ))

    async def make_into_news_channel(self) -> "NewsChannel":
        return NewsChannel.from_json(self._state, await self._edit(type=5))

    @classmethod
    def from_json(cls, state: State, json: dict) -> "GuildTextChannel":
        return GuildTextChannel(
            id=int(json["id"]),
            _state=state,
            position=int(json["position"]),
            name=json["name"],
            guild_id=int(json["guild_id"]),
            category_id=nullmap(json.get("parent_id"), int),
            topic=json.get("topic"),
            slowmode_seconds=int(json["rate_limit_per_user"])
        )


@dataclass(frozen=True)
class NewsChannel(TextChannel, GuildChannel, HasPosition):
    category_id: Optional[int]
    topic: Optional[str]

    async def start_thread(
        self,
        name: str,
        auto_archive_duration: AutoArchiveDuration = AutoArchiveDuration.ONE_DAY,
    ):
        await res.start_thread_without_message(
            self._state.http,
            channel_id=self.id,
            name=name,
            type=10,
            auto_archive_duration=auto_archive_duration
        )

    async def edit(
        self,
        *,
        name: U[str] = UNSET,
        position: U[int] = UNSET,
        topic: U[Optional[str]] = UNSET,
        nsfw: U[bool] = UNSET,
        category: U[Union["Category", int]] = UNSET,
        default_auto_archive_duration_minutes: U[int] = UNSET,
        permission_overwrites: U[Iterable[PermissionOverwrite]] = UNSET,
    ) -> "NewsChannel":
        if isinstance(category, Category):
            category = category.id

        return self.from_json(self._state, await self._edit(
            name=name,
            position=position,
            topic=topic,
            nsfw=nsfw,
            category=category,
            default_auto_archive_duration=default_auto_archive_duration_minutes,
            permission_overwrites=
                UNSET if isinstance(permission_overwrites, _UNSET)
                else [o.to_json() for o in permission_overwrites]
        ))

    async def make_into_text_channel(self) -> GuildTextChannel:
        return GuildTextChannel.from_json(self._state, await self._edit(type=0))

    @classmethod
    def from_json(cls, state: State, json: dict) -> "NewsChannel":
        return NewsChannel(
            id=int(json["id"]),
            _state=state,
            position=json["position"],
            name=json["name"],
            guild_id=int(json["guild_id"]),
            category_id=nullmap(json.get("parent_id"), int),
            topic=json.get("toic"),
        )


@dataclass(frozen=True)
class VoiceChannel(GuildChannel):
    bitrate: int
    user_limit: int
    rtc_region: Optional[str]


@dataclass(frozen=True)
class NormalVoiceChannel(VoiceChannel, HasPosition):
    video_quality_mode: Optional[VideoQualityMode]

    async def edit(
        self, *,
        name: U[str] = UNSET,
        position: U[int] = UNSET,
        category: U[Union["Category", int]] = UNSET,
        bitrate: U[int] = UNSET,
        default_auto_archive_duration_minutes: U[int] = UNSET,
        permission_overwrites: U[Iterable[PermissionOverwrite]] = UNSET,
        video_quality_mode: U[VideoQualityMode] = UNSET,
    ) -> "NormalVoiceChannel":
        if isinstance(category, Category):
            category = category.id

        return self.from_json(self._state, await self._edit(
            name=name,
            position=position,
            category=category,
            default_auto_archive_duration=default_auto_archive_duration_minutes,
            permission_overwrites=
                UNSET if isinstance(permission_overwrites, _UNSET)
                else [o.to_json() for o in permission_overwrites],
            bitrate=bitrate,
            video_quality_mode=video_quality_mode
        ))

    @classmethod
    def from_json(cls, state: State, json: dict) -> "NormalVoiceChannel":
        return NormalVoiceChannel(
            id=int(json["int"]),
            _state=state,
            name=json["name"],
            position=json["position"],
            guild_id=int(json["guild_id"]),
            bitrate=json["bitrate"],
            user_limit=json["user_limit"],
            rtc_region=json.get("rtc_region"),
            video_quality_mode=VideoQualityMode(json["video_qualify_mode"])
        )


@dataclass(frozen=True)
class Stage(VoiceChannel, HasPosition):
    topic: Optional[str]

    @classmethod
    def from_json(cls, state: State, json: dict) -> "Stage":
        return Stage(
            id=int(json["int"]),
            _state=state,
            name=json["name"],
            position=json["position"],
            guild_id=int(json["guild_id"]),
            bitrate=json["bitrate"],
            user_limit=json["user_limit"],
            rtc_region=json.get("rtc_region"),
            topic=json.get("topic")
        )


_TC = TypeVar("_TC", bound="Thread")


def _parse_thread_metadata(json: dict):
    return {
        **json,
        "auto_archive_duration ": AutoArchiveDuration(json["auto_archive_duration"]),
        "archive_timestamp": datetime.fromisoformat(json["archive_timestamp"]),
    }


@dataclass(frozen=True)
class _ThreadMemberObj:
    thread_id: int
    user_id: int
    join_timestamp: datetime
    flags: int

    @staticmethod
    def from_json(json) -> "_ThreadMemberObj":
        return _ThreadMemberObj(
            thread_id=int(json["id"]),
            user_id=int(json["user_id"]),
            join_timestamp=datetime.fromisoformat(json["join_timestamp"]),
            flags=int(json["flags"]),
        )


@dataclass(frozen=True)
class ThreadMembers:
    id: int
    _state: State

    async def add(self, member: Union[Snowflake, int]):
        await res.add_thread_member(
            self._state.http,
            channel_id=self.id,
            user_id=extract_int(member)
        )

    async def remove(self, member: Union[Snowflake, int]):
        await res.add_thread_member(
            self._state.http,
            channel_id=self.id,
            user_id=extract_int(member)
        )

    async def fetch(self) -> AsyncIterator[Member]:
        for json in await res.list_thread_members(
            self._state.http,
            channel_id=self.id,
        ):
            member_obj = _ThreadMemberObj.from_json(json)
            yield Member(member_obj.user_id)


@dataclass(frozen=True)
class Thread(TextChannel, GuildChannel):
    parent_channel_id: int
    slowmode_seconds: int
    owner_id: int
    joined_at: Optional[datetime]

    archived: bool
    auto_archive_duration: AutoArchiveDuration
    archive_timestamp: bool
    locked: bool

    async def join(self):
        await res.join_thread(self._state.http, channel_id=self.id)

    async def leave(self):
        await res.leave_thread(self._state.http, channel_id=self.id)

    def members(self) -> ThreadMembers:
        return ThreadMembers(self.id, self._state)

    async def edit(
        self: _TC,
        *,
        name: U[str] = UNSET,
        archived: U[bool] = UNSET,
        auto_archive_duration: U[AutoArchiveDuration] = UNSET,
        locked: U[bool] = UNSET,
        invitable: U[bool] = UNSET,
        slowmode_seconds:  U[int] = UNSET,
    ) -> _TC:
        return self.from_json(self._state, await res.modify_thread_channel(
            http=self._state.http,
            channel_id=self.id,
            name=name,
            archived=archived,
            auto_archive_duration=auto_archive_duration,
            locked=locked,
            invitable=invitable,
            rate_limit_per_user=slowmode_seconds,
        ))

    @classmethod
    def from_json(cls: Type[_TC], state: State, json: dict) -> _TC:
        return cls(
            id=int(json["id"]),
            _state=state,
            guild_id=int(json["guild_id"]),
            parent_channel_id=int(json["parent_channel_id"]),
            name=json["name"],
            slowmode_seconds=json["rate_limit_per_user"],
            owner_id=int(json["owner_id"]),
            joined_at=nullmap(
                json.get("member"),
                lambda member_obj: datetime.fromisoformat(member_obj["join_timestamp"])
            ),
            **_parse_thread_metadata(json)
        )


class PublicThread(Thread):
    pass


@dataclass(frozen=True)
class PrivateThread(Thread):
    invitable: bool


class NewsChannelThread(Thread):
    pass


@dataclass(frozen=True)
class Category(GuildChannel, HasPosition):
    @classmethod
    def from_json(cls, state: State, json: dict) -> "Category":
        return Category(
            id=int(json["id"]),
            _state=state,
            guild_id=int(json["guild_id"]),
            position=json["position"],
            name=json["name"],
        )


@dataclass(frozen=True)
class StoreChannel(GuildChannel, HasPosition):
    async def edit(
        self, *,
        name: U[str] = UNSET,
        nsfw: U[bool] = UNSET,
        category: U[Union[Category, int]] = UNSET,
        position: U[int] = UNSET,
        permission_overwrites: U[Iterable[PermissionOverwrite]] = UNSET,
    ) -> "StoreChannel":
        if isinstance(category, Category):
            category = category.id

        return self.from_json(self._state, await self._edit(
            name=name,
            position=position,
            permission_overwrites=
                UNSET if isinstance(permission_overwrites, _UNSET)
                else [o.to_json() for o in permission_overwrites],
            nsfw=nsfw,
            category=category,
        ))

    @classmethod
    def from_json(cls, state: State, json: dict) -> "StoreChannel":
        return StoreChannel(
            id=int(json["id"]),
            _state=state,
            guild_id=int(json["guild_id"]),
            position=json["position"],
            name=json["name"],
        )


_CHANNEL_TYPE_TO_CLASS: Dict[int, Type[Channel]] = {
    0: GuildTextChannel,
    1: DMChannel,
    2: NormalVoiceChannel,
    4: Category,
    5: NewsChannel,
    6: StoreChannel,
    10: NewsChannelThread,
    11: PublicThread,
    12: PrivateThread,
    13: Stage
}
