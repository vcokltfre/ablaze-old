from json import loads
from typing import Optional, Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..file import File
from ..route import Route


async def create_webhook(
    http: RESTClient, channel_id: int, name: str, avatar: Union[str, _UNSET] = UNSET
) -> dict:
    route = Route("/channels/{channel_id}/webhooks", channel_id=channel_id)
    params = http.get_params(
        name=name,
        avatar=avatar,
    )

    return await http.post(route, json=params)


async def get_channel_webhooks(http: RESTClient, channel_id: int) -> list:
    route = Route("/channels/{channel_id}/webhooks", channel_id=channel_id)

    return await http.get(route)


async def get_guild_webhooks(http: RESTClient, guild_id: int) -> list:
    route = Route("/guilds/{guild_id}/webhooks", guild_id=guild_id)

    return await http.get(route)


async def get_webhook(http: RESTClient, webhook_id: int) -> dict:
    route = Route("/webhooks/{webhook_id}", webhook_id=webhook_id)

    return await http.get(route)


async def get_webhook_with_token(
    http: RESTClient, webhook_id: int, webhook_token: str
) -> dict:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
    )

    return await http.get(route)


async def modify_webhook(
    http: RESTClient,
    webhook_id: int,
    name: Union[str, _UNSET] = UNSET,
    avatar: Union[str, _UNSET] = UNSET,
    channel_id: Union[int, _UNSET] = UNSET,
) -> dict:
    route = Route("/webhooks/{webhook_id}", webhook_id=webhook_id)
    params = http.get_params(
        name=name,
        avatar=avatar,
        channel_id=channel_id,
    )

    return await http.patch(route, json=params)


async def modify_webhook_with_token(
    http: RESTClient,
    webhook_id: int,
    webhook_token: str,
    name: Union[str, _UNSET] = UNSET,
    avatar: Union[str, _UNSET] = UNSET,
    channel_id: Union[int, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
    )
    params = http.get_params(
        name=name,
        avatar=avatar,
        channel_id=channel_id,
    )

    return await http.patch(route, json=params)


async def delete_webhook(http: RESTClient, webhook_id: int) -> None:
    route = Route("/webhooks/{webhook_id}", webhook_id=webhook_id)

    await http.delete(route, format="none")


async def delete_webhook_with_token(
    http: RESTClient, webhook_id: int, webhook_token: str
) -> None:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
    )

    await http.delete(route, format="none")


async def execute_webhook(
    http: RESTClient,
    webhook_id: int,
    webhook_token: str,
    wait: Union[bool, _UNSET] = UNSET,
    thread_id: Union[int, _UNSET] = UNSET,
    content: Union[str, _UNSET] = UNSET,
    avatar_url: Union[str, _UNSET] = UNSET,
    tts: Union[bool, _UNSET] = UNSET,
    file: Union[File, _UNSET] = UNSET,
    embeds: Union[list, _UNSET] = UNSET,
    allowed_mentions: Union[dict, _UNSET] = UNSET,
    components: Union[list, _UNSET] = UNSET,
) -> Optional[dict]:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
    )
    qparams = http.get_params(
        wait=wait,
        thread_id=thread_id,
    )
    params = http.get_params(
        content=content,
        avatar_url=avatar_url,
        tts=tts,
        embeds=embeds,
        allowed_mentions=allowed_mentions,
        components=components,
    )

    # The `wait` flag specifies whether Discord should confirm the execution
    # by returning a message object back.
    result = await http.post(route, files=[file], json=params, qparams=qparams, format="text")
    if result:
        return loads(result)
    else:
        return None


async def get_webhook_message(
    http: RESTClient, webhook_id: int, webhook_token: str, message_id: int
) -> dict:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
        message_id=message_id,
    )

    return await http.get(route)


async def edit_webhook_message(
    http: RESTClient,
    webhook_id: int,
    webhook_token: str,
    message_id: int,
    content: Union[str, _UNSET] = UNSET,
    file: Union[File, _UNSET] = UNSET,
    embeds: Union[list, _UNSET] = UNSET,
    allowed_mentions: Union[dict, _UNSET] = UNSET,
    attachments: Union[list, _UNSET] = UNSET,
    components: Union[list, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
        message_id=message_id,
    )
    params = http.get_params(
        content=content,
        embeds=embeds,
        allowed_mentions=allowed_mentions,
        attachments=attachments,
        components=components,
    )

    return await http.patch(route, files=[file], json=params)


async def delete_webhook_message(
    http: RESTClient, webhook_id: int, webhook_token: str, message_id: int
) -> None:
    route = Route(
        "/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}",
        webhook_id=webhook_id,
        webhook_token=webhook_token,
        message_id=message_id,
    )

    await http.delete(route, format="none")
