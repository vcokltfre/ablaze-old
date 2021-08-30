from ablaze.objects.permissions import PermissionFlags
from datetime import datetime
from ablaze.objects.user import User
from enum import IntEnum
from typing import Any, Callable, Dict, Iterable, Optional, Type, TypeVar, Union
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


def _nullmap(optional: Optional[_T], fn: Callable[[_T], _R]) -> Optional[_R]:
    if optional is None:
        return None
    return fn(optional)


@dataclass(frozen=True)
class State:
    http: RESTClient
    cache: Callable[[int], Optional["Channel"]]


def channel_from_json(state: State, json: dict):
    channel_type = _CHANNEL_TYPE_TO_CLASS[json["type"]]
    return channel_type.from_json(state, json)


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

    @classmethod
    @abstractmethod
    def from_json(cls: Type[_C], state: State, json: dict) -> _C:
        ...


class TextChannel(Channel):
    # TODO: implement the Message object
    async def send(self, yolo: dict) -> dict:
        return await res.create_message(
            self._state.http,
            channel_id=self.id,
            **yolo
        )


@dataclass(frozen=True)
class DMChannel(TextChannel):
    recipient: User

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
class HasPosition:
    position: int


@dataclass(frozen=True)
class GuildTextChannel(TextChannel, GuildChannel, HasPosition):
    category_id: Optional[int]
    topic: Optional[str]
    slowmode_seconds: int

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
            category_id=_nullmap(json.get("parent_id"), int),
            topic=json.get("topic"),
            slowmode_seconds=int(json["rate_limit_per_user"])
        )


@dataclass(frozen=True)
class NewsChannel(TextChannel, GuildChannel, HasPosition):
    category_id: Optional[int]
    topic: Optional[str]

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
            category_id=_nullmap(json.get("parent_id"), int),
            topic=json.get("toic"),
        )


class VideoQualityMode(IntEnum):
    AUTO = 1
    FULL = 2


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


class AutoArchiveDuration(IntEnum):
    HOUR = 60
    ONE_DAY = 1440
    THREE_DAYS = 4320
    SEVEN_DAYS = 10080


_TC = TypeVar("_TC", bound="Thread")


def _parse_thread_metadata(json: dict):
    return {
        **json,
        "auto_archive_duration ": AutoArchiveDuration(json["auto_archive_duration"]),
        "archive_timestamp": datetime.fromisoformat(json["archive_timestamp"]),
    }


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
            joined_at=_nullmap(
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
