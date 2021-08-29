from typing import Union

from .abc import Snowflake
from .assets import UserAvatar, DefaultUserAvatar
from .flags import PublicUserFlags


class User(Snowflake):
    def __init__(self, data: dict) -> None:
        self._raw = data

        self.id: int = data["id"]
        self.username: str = data["username"]
        self.discriminator: int = int(data["discriminator"])

        avatar = UserAvatar(self.id, data["avatar"]) if data.get("avatar") else DefaultUserAvatar(self.discriminator)
        self.avatar: Union[UserAvatar, DefaultUserAvatar] = avatar

        self.bot: bool = data.get("bot", False)
        self.flags = PublicUserFlags(data.get("public_flags", 0))
