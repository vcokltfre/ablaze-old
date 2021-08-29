from typing import Union, Optional

from .abc import Snowflake
from .assets import UserAvatar, DefaultUserAvatar, UserBanner
from .flags import PublicUserFlags


class User(Snowflake):
    def __init__(self, data: dict) -> None:
        self._raw = data

        self.id: int = int(data["id"])
        self.username: str = data["username"]
        self.discriminator: int = int(data["discriminator"])

        avatar = UserAvatar(self.id, data["avatar"]) if data.get("avatar") else DefaultUserAvatar(self.discriminator)
        self.avatar: Union[UserAvatar, DefaultUserAvatar] = avatar

        banner = UserBanner(self.id, data["banner"]) if data.get("banner") else None
        self.banner: Optional[UserBanner] = banner

        self.bot: bool = data.get("bot", False)
        self.flags = PublicUserFlags(data.get("public_flags", 0))
        self.accent_colour = data.get("accent_colour", 0)
