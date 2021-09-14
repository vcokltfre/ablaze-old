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
    """
    Create a channel of the correct concrete class using a JSON
    response from Discord.
    """
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


@dataclass
class State:
    """
    State is required by Channel objects because they act in a
    sort of 'active record' way: they allow communicating
    over the network but don't rely on global state.
    """
    http: RESTClient
    cache: Cache


class AutoArchiveDuration(IntEnum):
    """
    The fixed values allowed by Discord to specify the archive duraiton.

    Archive duration is how much time must pass since the last message of
    a thread until it becomes archived.
    """
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


@dataclass
class PermissionOverwrite:
    """
    Data structure used to customize permissions for a single member or a role.

    Reference: https://discord.com/developers/docs/topics/permissions#permission-overwrites
    """
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


@dataclass
class Channel(ABC, Snowflake):
    """
    A channel is a node in the tree structure of a guild. This includes ordinary
    text channels, threads, voice channels, and categories.

    Reference: https://discord.com/developers/docs/resources/channel#channel-object

    This class is abstract -- you can't instantiate it.
    """
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
    Context manager for a typing indicator.
    """
    def __init__(self, refresh: Callable[[], Awaitable[None]]):
        self.stopped = False
        self.refresh = refresh
        self._task = asyncio.create_task(self.sleep_forever())

    async def sleep_forever(self):
        while not self.stopped:
            await self.refresh()
            # the typing indicator persists for 10 seconds, but if we refresh it
            # every 10 seconds theere's going to be a gap in the animation
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
    """
    A channel you can send a message into.

    This class is abstract -- you can't instantiate it.
    """
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
        """
        Delete many messages at once.

        Reference: <https://discord.com/developers/docs/resources/channel#bulk-delete-messages>
        """
        await res.bulk_delete_messages(
            self._state.http,
            channel_id=self.id,
            messages=[extract_int(m) for m in messages]
        )

    def typing(self) -> ContextManager:
        """
        Acquire a context manager that keeps the typing indicator ("<Bot> is typing...")
        as long as its body is running.

        >>> with channel.typing():
        ...     # do some long-running computation
        """
        async def refresh_typing():
            await res.trigger_typing_indicator(
                self._state.http,
                channel_id=self.id
            )
        return _Typing(refresh_typing)

    async def pinned_messages(self) -> Sequence[messages_module.Message]:
        """
        Fetch all messages that are pinned in this channel.

        This returns a sequence and not an asynchronous iterator because the API
        doesn't provide any pagination, as there can only be 100 pinned messages
        in a single channel.
        """
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


@dataclass
class DMChannel(TextChannel):
    """
    Pseudo-channel representing the direct message communication with a user.
    """
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


@dataclass
class GuildChannel(Channel):
    """
    Channel that is in a guild.

    This class is abstract -- you can't instantiate it.
    """
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


@dataclass
class HasPosition(Channel):
    """
    Mixin signalling that a channel has a position in some ordered list
    """
    position: int


@dataclass
class GuildTextChannel(TextChannel, GuildChannel, HasPosition):
    """
    Ordinary text channel in a guild, denoted in Discord as #<name>.
    """
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


@dataclass
class NewsChannel(TextChannel, GuildChannel, HasPosition):
    """
    Called "announcement channels" on the platform.

    This type of channel supports subscriptions. They work like this:
    - A usser can make a channel on their server follow a news channel. ``
    - Following is implemented via a webhook, which is represented with
      `ChannelFollowerWebhook` in this library.
    - A user who is allowed to send a message in the news channel can publish it.
      In that case, this message is executed on all follower webhooks.
    """
    # TODO: following

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


@dataclass
class VoiceChannel(GuildChannel):
    """
    Either a 'normal' voice channel or a stage channel.
    """
    bitrate: int
    user_limit: int
    rtc_region: Optional[str]


@dataclass
class NormalVoiceChannel(VoiceChannel, HasPosition):
    """
    Channel where users can communicate via voice and/or video.
    """
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


@dataclass
class Stage(VoiceChannel, HasPosition):
    """
    Stage channel for one-to-many communication.
    """
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


@dataclass
class _ThreadMemberObj:
    """
    Reference: <https://discord.com/developers/docs/resources/channel#thread-member-object>
    """
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


@dataclass
class ThreadMembers:
    """
    Helper object for working with thread members
    """
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


@dataclass
class Thread(TextChannel, GuildChannel):
    """
    Temporary sub-channel inside a text channel.
    """
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
    """
    Public thread created on a guild text channel
    """


@dataclass
class PrivateThread(Thread):
    """
    Private thread created on a guild text channel
    """
    invitable: bool


class NewsChannelThread(Thread):
    """
    Public thread created on a news channel
    """


@dataclass
class Category(GuildChannel, HasPosition):
    """
    Pseudo-channel representing a category on the platform.

    A category is a root for text channels, voice channels, stage
    channels and news chanenls.
    """

    @classmethod
    def from_json(cls, state: State, json: dict) -> "Category":
        return Category(
            id=int(json["id"]),
            _state=state,
            guild_id=int(json["guild_id"]),
            position=json["position"],
            name=json["name"],
        )


@dataclass
class StoreChannel(GuildChannel, HasPosition):
    # Store channels are out of scope for now because they're not
    # easily available for testing

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
