from enum import IntEnum
from typing import Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..route import Route


class PrivacyLevel(IntEnum):
    PUBLIC = 1
    GUILD_ONLY = 2


async def create_stage_instance(
    http: RESTClient,
    channel_id: int,
    topic: str,
    privacy_level: PrivacyLevel = PrivacyLevel.GUILD_ONLY,
) -> dict:
    route = Route("/stage-instance")

    return await http.post(
        route,
        json={
            "channel_id": channel_id,
            "topic": topic,
            "privacy_level": privacy_level,
        },
    )


async def get_stage_instance(
    http: RESTClient,
    channel_id: int,
) -> dict:
    route = Route("/stage-instance/{channel_id}", channel_id=channel_id)

    return await http.get(route)


async def modify_stage_instance(
    http: RESTClient,
    channel_id: int,
    topic: Union[str, _UNSET] = UNSET,
    privacy_level: Union[PrivacyLevel, _UNSET] = UNSET,
) -> dict:
    route = Route("/stage-instance/{channel_id}", channel_id=channel_id)

    return await http.patch(
        route,
        json=http.get_params(
            topic=topic,
            privacy_level=privacy_level,
        ),
    )


async def delete_stage_instance(
    http: RESTClient,
    channel_id: int,
) -> None:
    route = Route("/stage-instance/{channle_id}", channel_id=channel_id)

    await http.delete(route, format="none")
