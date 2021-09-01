from abc import ABC, abstractmethod
from ablaze.objects.utils import extract_int
from dataclasses import dataclass
from ablaze.internal.http.file import File
from typing import Any, Dict, Optional, Sequence, Union
from ablaze.objects.abc import Snowflake


@dataclass(frozen=True)
class RenderedMessageContent:
    json: Dict[str, Any]
    file: Optional[File]


class BaseMessageContent(ABC):
    @abstractmethod
    def render(self) -> RenderedMessageContent: ...

    def in_reply_to(self, to: Union[Snowflake, int]) -> "MessageContentWithReference":
        return MessageContentWithReference(self, to)


@dataclass(frozen=True)
class MessageContent(BaseMessageContent):
    text: Optional[str] = None
    embeds: Optional[Sequence[Any]] = None  # TODO: embeds
    allowed_mentions: Optional[Any] = None  # TODO: allowed mentions
    components: Optional[Sequence[Any]] = None  # TODO: component
    stickers: Optional[Sequence[Union[Snowflake, int]]] = None
    tts: Optional[bool] = False
    file: Optional[File] = None

    def __post_init__(self):
        if not (self.text or self.embeds or self.stickers or self.file):
            raise ValueError("You must provide at least one of {text, stickers, embeds, file}")

    def render(self) -> RenderedMessageContent:
        json = {}
        if self.text:
            json["content"] = self.text
        if self.embeds:
            json["embeds"] = [embed for embed in self.embeds]
        if self.allowed_mentions:
            json["allowed_mentions"] = self.allowed_mentions
        if self.components:
            json["components"] = [component for component in self.components]
        if self.stickers:
            json["sticker_ids"] = [extract_int(sticker) for sticker in self.stickers]
        if self.tts is not None:
            json["tts"] = self.tts

        return RenderedMessageContent(json=json, file=self.file)


@dataclass(frozen=True)
class MessageContentWithReference(BaseMessageContent):
    base: BaseMessageContent
    message_reference: Union[Snowflake, int]

    def render(self) -> RenderedMessageContent:
        rendered_base = self.base.render()
        json = {
            **rendered_base.json,
            "message_reference": {
                "message_id": extract_int(self.message_reference),
            }
        }
        return RenderedMessageContent(json=json, file=rendered_base.file)


@dataclass(frozen=True)
class Message(Snowflake):
    id: int
    text: Optional[str]

    @staticmethod
    def from_json(json: dict) -> "Message":
        return Message(
            id=int(json["id"]),
            text=json.get("content")
        )
