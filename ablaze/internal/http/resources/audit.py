from ...utils import UNSET
from ..client import RESTClient
from ..route import Route


async def get_guild_audit_log(
    http: RESTClient,
    guild_id: int,
    user_id: int = UNSET,
    action_type: int = UNSET,
    before: int = UNSET,
    limit: int = UNSET,
) -> dict:
    route = Route("/guilds/{guild_id}/audit-logs", guild_id=guild_id)
    params = http._get_params(
        user_id=user_id, action_type=action_type, before=before, limit=limit
    )

    return await (await http.get(route, qparams=params)).json()
