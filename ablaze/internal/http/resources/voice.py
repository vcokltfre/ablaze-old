from typing import Dict, List

from ..client import RESTClient
from ..route import Route


async def list_voice_regions(http: RESTClient) -> List[Dict]:
    route = Route("/voice/regions")

    return await http.get(route)
