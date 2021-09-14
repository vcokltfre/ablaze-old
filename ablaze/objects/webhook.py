from dataclasses import dataclass
from typing import Dict, Optional, Type, TypeVar, Union

import ablaze.internal.http.resources.webhook as res
import ablaze.objects.messages as messages
from ablaze.internal.http.client import RESTClient
from ablaze.internal.utils import _UNSET, UNSET
from ablaze.objects.abc import Snowflake
from ablaze.objects.utils import extract_int, nullmap, unsetmap


def webhook_from_json(client: RESTClient, json: dict) -> "Webhook":
    cls = _WEBHOOK_TYPE_TO_CLASS[json["type"]]
    return cls.from_json(client, json)


_W = TypeVar("_W", bound="Webhook")


@dataclass
class Webhook(Snowflake):
    id: int
    _http: RESTClient
    name: str
    application_id: Optional[int]
    avatar_hash: Optional[str]
    channel_id: Optional[int]
    guild_id: Optional[int]

    async def delete(self) -> None:
        await res.delete_webhook(self._http, webhook_id=self.id)

    async def edit(
        self: _W,
        name: Union[str, _UNSET] = UNSET,
        avatar_hash: Union[str, _UNSET] = UNSET,
        channel: Union[Snowflake, int, _UNSET] = UNSET,
    ) -> _W:
        return self.from_json(
            self._http,
            await res.modify_webhook(
                self._http,
                webhook_id=self.id,
                name=name,
                avatar=avatar_hash,
                channel_id=channel.id if isinstance(channel, Snowflake) else channel,
            ),
        )

    @staticmethod
    def from_json(client: RESTClient, json: dict) -> "Webhook":
        return Webhook(
            id=int(json["int"]),
            _http=client,
            name=json["name"],
            application_id=nullmap(json["application_id"], int),
            avatar_hash=json["avatar"],
            channel_id=nullmap(json["channel_id"], int),
            guild_id=nullmap(json["guild_id"], int),
        )


@dataclass
class SourceChannel(Snowflake):
    id: int
    name: str

    @staticmethod
    def from_json(json: dict) -> "SourceChannel":
        return SourceChannel(id=int(json["int"]), name=json["name"])


@dataclass
class SourceGuild(Snowflake):
    id: int
    name: str
    icon_hash: Optional[str]

    @staticmethod
    def from_json(json: dict) -> "SourceGuild":
        return SourceGuild(
            id=int(json["int"]), name=json["name"], icon_hash=json["icon"]
        )


@dataclass
class IncomingWebhook(Webhook):
    """
    'Normal' webhook created in the 'manage channel' screen.
    """

    token: str

    async def send(
        self,
        content: "messages.BaseMessageContent",
        thread: Union[Snowflake, int, _UNSET] = UNSET,
    ) -> "messages.Message":
        """Execute the webhook.

        :param thread: If provided, message will be sent to a thread in the channel
        :return: Message object representing the sent message
        """
        rendered = content.render()

        if "sticker_ids" in rendered.json:
            raise ValueError("Cannot send stickers over a webhook")

        message_json = await res.execute_webhook(
            self._http,
            webhook_id=self.id,
            webhook_token=self.token,
            file=rendered.file or UNSET,
            wait=True,
            thread_id=unsetmap(thread, extract_int),
            **rendered.json,
        )
        assert message_json is not None  # because `wait` is enabled
        return messages.Message.from_json(message_json)

    async def send_nowait(
        self,
        content: "messages.BaseMessageContent",
        thread: Union[Snowflake, int, _UNSET] = UNSET,
    ) -> None:
        """Execute the webhook, but don't wait for a response.

        :param thread: If provided, message will be sent to a thread in the channel
        :return: None
        """
        rendered = content.render()

        if "sticker_ids" in rendered.json:
            raise ValueError("Cannot send stickers over a webhook")

        await res.execute_webhook(
            self._http,
            webhook_id=self.id,
            webhook_token=self.token,
            file=rendered.file or UNSET,
            wait=False,
            thread_id=unsetmap(thread, extract_int),
            **rendered.json,
        )

    @staticmethod
    def from_json(client: RESTClient, json: dict) -> "IncomingWebhook":
        return IncomingWebhook(
            **super().from_json(client, json).__dict__, token=json["token"]
        )


@dataclass
class ChannelFollowerWebhook(Webhook):
    """Internal webhook that Discord uses to implement following a news channel"""

    channel_id: int
    guild_id: int
    source_channel: SourceChannel
    source_guild: SourceGuild

    @staticmethod
    def from_json(client: RESTClient, json: dict) -> "ChannelFollowerWebhook":
        return ChannelFollowerWebhook(
            **super().from_json(client, json).__dict__,
            source_channel=SourceChannel.from_json(json["source_channel"]),
            source_guild=SourceGuild.from_json(json["source_guild"]),
        )


@dataclass
class ApplicationWebhook(Webhook):
    """Application webhooks are webhooks used with Interactions."""

    application_id: int  # should always be non-None

    @staticmethod
    def from_json(client: RESTClient, json: dict) -> "ApplicationWebhook":
        return ApplicationWebhook(
            **super().from_json(client, json).__dict__,
        )


_WEBHOOK_TYPE_TO_CLASS: Dict[int, Type[Webhook]] = {
    1: IncomingWebhook,
    2: ChannelFollowerWebhook,
    3: ApplicationWebhook,
}
