from ..client import RESTClient
from ..route import Route


async def get_gateway(http: RESTClient) -> dict:
    route = Route("/gateway")

    return await (await http.get(route)).json()


async def get_gateway_bot(http: RESTClient) -> dict:
    route = Route("/gateway/bot")

    return await (await http.get(route)).json()
