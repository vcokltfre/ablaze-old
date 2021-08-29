from ..client import RESTClient
from ..route import Route


async def get_invite(http: RESTClient, invite_code: str) -> dict:
    route = Route("/invites/{invite_code}", invite_code=invite_code)

    return await http.get(route)


async def delete_invite(http: RESTClient, invite_code: str) -> None:
    route = Route("/invites/{invite_code}", invite_code=invite_code)

    await http.delete(route, format="none")
