from ..client import RESTClient
from ..route import Route


async def get_gateway(http: RESTClient) -> dict:
    route = Route("/gateway")

    return await http.get(route)


async def get_gateway_bot(http: RESTClient) -> dict:
    route = Route("/gateway/bot")

    return await http.get(route)
