from typing import List, Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..route import Route


async def get_current_user(http: RESTClient) -> dict:
    route = Route("/users/@me")

    return await http.get(route)


async def get_user(http: RESTClient, user_id: int) -> dict:
    route = Route("/users/{user_id}", user_id=user_id)

    return await http.get(route)


async def modify_current_user(
    http: RESTClient,
    username: Union[str, _UNSET] = UNSET,
    avatar_base64: Union[str, _UNSET] = UNSET,
) -> dict:
    route = Route("/users/@me")

    return await http.patch(
        route,
        json=http.get_params(
            username=username,
            avatar_base64=avatar_base64,
        ),
    )


async def get_current_user_guilds(
    http: RESTClient,
    before: Union[int, _UNSET] = UNSET,
    after: Union[int, _UNSET] = UNSET,
    limit: int = 200,
) -> List[dict]:
    route = Route("/users/@me/guilds")

    return await http.get(
        route,
        qparams=http.get_params(
            before=before,
            after=after,
            limit=limit,
        ),
    )


async def leave_guild(
    http: RESTClient,
    guild_id: int,
) -> None:
    route = Route("/users/@me/guilds/{guild_id}", guild_id=guild_id)

    await http.delete(route, format="none")


async def create_dm(
    http: RESTClient,
    recipient_id: int,
) -> dict:
    route = Route("/users/@me/channels")

    return await http.post(
        route,
        json={
            "recipient_id": recipient_id,
        },
    )
