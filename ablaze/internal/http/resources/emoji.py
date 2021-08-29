from typing import Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..route import Route


async def list_guild_emojis(http: RESTClient, guild_id: int) -> list:
    route = Route("/guilds/{guild_id}/emojis", guild_id=guild_id)

    return await http.get(route)


async def get_guild_emoji(http: RESTClient, guild_id: int, emoji_id: int) -> dict:
    route = Route(
        "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id
    )

    return await http.get(route)


async def create_guild_emoji(
    http: RESTClient,
    guild_id: int,
    name: str,
    image: str,
    roles: list = [],
    *,
    reason: str = None,
) -> dict:
    route = Route("/guilds/{guild_id}/emojis", guild_id=guild_id)
    params = http._get_params(
        name=name,
        image=image,
        roles=roles,
    )

    return await http.post(route, json=params, reason=reason)


async def modify_guild_emoji(
    http: RESTClient,
    guild_id: int,
    emoji_id: int,
    name: Union[str, _UNSET] = UNSET,
    roles: Union[list, _UNSET] = UNSET,
    *,
    reason: str = None,
) -> dict:
    route = Route(
        "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id
    )
    params = http._get_params(
        name=name,
        roles=roles,
    )

    return await http.get(route, json=params, reason=reason)


async def delete_guild_emoji(
    http: RESTClient, guild_id: int, emoji_id: int, *, reason: str = None
) -> None:
    route = Route(
        "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id
    )

    await http.delete(route, reason=reason, format="none")
