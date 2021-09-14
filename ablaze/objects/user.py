from dataclasses import dataclass
from typing import Optional, Union

from .abc import Snowflake
from .assets import DefaultUserAvatar, UserAvatar, UserBanner
from .flags import PublicUserFlags


@dataclass
class User(Snowflake):
    id: int
    username: str
    discriminator: int
    avatar: Optional[UserAvatar]
    default_avatar: DefaultUserAvatar
    banner: Optional[UserBanner]
    bot: bool
    public_flags: PublicUserFlags
    accent_colour: int

    @classmethod
    def from_json(cls, json: dict) -> "User":
        id = int(json["id"])
        discriminator = int(json["discriminator"])

        avatar = None
        if avatar_hash := json.get("avatar"):
            avatar = UserAvatar(int(id), avatar_hash)

        banner = None
        if banner_hash := json.get("banner"):
            banner = UserBanner(int(id), banner_hash)

        return cls(
            id=id,
            username=json["username"],
            discriminator=discriminator,
            avatar=avatar,
            default_avatar=DefaultUserAvatar(discriminator),
            banner=banner,
            bot=json.get("bot", False),
            public_flags=PublicUserFlags(json.get("public_flags", 0)),
            accent_colour=json.get("accent_colour", 0),
        )

    def __str__(self) -> str:
        return f"{self.username}#{self.discriminator}"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: "User") -> bool:
        return other.id == self.id
