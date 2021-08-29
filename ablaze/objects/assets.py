from typing import Literal

from .abc import Snowflake

CDN_URL = "https://cdn.discordapp.com/"


class Emoji(Snowflake):
    def __init__(self, id: int, name: str, animated: bool) -> None:
        self.id = id
        self.name = name
        self.animated = animated

    def url_as(self, format: Literal["jpg", "png", "webp", "gif"]) -> str:
        return CDN_URL + f"{self.id}.{format}"


class IDHashAsset:
    resource: str

    def __init__(self, id: int, hash: str) -> None:
        self.id = id
        self.hash = hash

    def url_as(self, format: Literal["jpg", "png", "webp"]) -> str:
        return CDN_URL + f"{self.resource}/{self.id}/{self.hash}.{format}"


class GuildIcon(IDHashAsset):
    resource = "icons"

    def url_as(self, format: Literal["jpg", "png", "webp", "gif"]) -> str:
        return CDN_URL + f"{self.resource}/{self.id}/{self.hash}.{format}"


class GuildSplash(IDHashAsset):
    resource = "splashes"


class GuildDiscoverySplash(IDHashAsset):
    resource = "discovery-splashes"


class GuildBanner(IDHashAsset):
    resource = "banners"


class UserBanner(IDHashAsset):
    resource = "banners"


class DefaultUserAvatar:
    def __init__(self, discriminator: int) -> None:
        self.discriminator = discriminator

        self.url = CDN_URL + f"/embed/avatars/{self.discriminator % 5}.png"


class UserAvatar(IDHashAsset):
    resource = "avatars"

    def url_as(self, format: Literal["jpg", "png", "webp", "gif"]) -> str:
        return CDN_URL + f"{self.resource}/{self.id}/{self.hash}.{format}"


class ApplicationIcon(IDHashAsset):
    resource = "app-icons"


class ApplicationCover(IDHashAsset):
    resource = "app-icons"


class ApplicationAsset:
    def __init__(self, application_id: int, asset_id: int) -> None:
        self.application_id = application_id
        self.asset_id = asset_id

    def url_as(self, format: Literal["jpg", "png", "webp"]) -> str:
        return CDN_URL + f"app-assets/{self.application_id}/{self.asset_id}.{format}"


class AchievementIcon:
    def __init__(self, application_id: int, achievement_id: int, hash: str) -> None:
        self.application_id = application_id
        self.achievement_id = achievement_id
        self.hash = hash

    def url_as(self, format: Literal["jpg", "png", "webp"]) -> str:
        return (
            CDN_URL
            + f"app-assets/{self.application_id}/achievements/{self.achievement_id}/icons/{self.hash}.{format}"
        )


class StickerPackBanner:
    def __init__(self, asset_id: int) -> None:
        self.asset_id = asset_id

    def url_as(self, format: Literal["jpg", "png", "webp"]) -> str:
        return CDN_URL + f"app-assets/710982414301790216/store/{self.asset_id}.{format}"


class TeamIcon(IDHashAsset):
    def __init__(self, id: int, hash: str) -> None:
        self.id = id
        self.hash = hash

    def url_as(self, format: Literal["jpg", "png", "webp"]) -> str:
        return CDN_URL + f"team-icons/{self.id}/{self.hash}.{format}"


class Sticker:
    def __init__(self, id: int) -> None:
        self.id = id

    def url_as(self, format: Literal["png", "lottie"]) -> str:
        return CDN_URL + f"stickers/{self.id}.{format}"
