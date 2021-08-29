from typing import Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..route import Route


async def get_guild_audit_log(
    http: RESTClient,
    guild_id: int,
    user_id: Union[int, _UNSET] = UNSET,
    action_type: Union[int, _UNSET] = UNSET,
    before: Union[int, _UNSET] = UNSET,
    limit: Union[int, _UNSET] = UNSET,
) -> dict:
    route = Route("/guilds/{guild_id}/audit-logs", guild_id=guild_id)
    params = http._get_params(
        user_id=user_id, action_type=action_type, before=before, limit=limit
    )

    return await http.get(route, qparams=params)
