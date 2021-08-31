from typing import Union
from urllib.parse import quote
from warnings import warn

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..file import File
from ..route import Route


async def get_channel(http: RESTClient, channel_id: int) -> dict:
    route = Route("/channels/{channel_id}", channel_id=channel_id)

    return await http.get(route)


async def modify_guild_channel(
    http: RESTClient,
    channel_id: int,
    name: Union[str, _UNSET] = UNSET,
    type: Union[int, _UNSET] = UNSET,
    position: Union[int, _UNSET] = UNSET,
    topic: Union[str, _UNSET] = UNSET,
    nsfw: Union[bool, _UNSET] = UNSET,
    rate_limit_per_user: Union[int, _UNSET] = UNSET,
    bitrate: Union[int, _UNSET] = UNSET,
    user_limit: Union[int, _UNSET] = UNSET,
    permission_overwrites: Union[list, _UNSET] = UNSET,
    parent_id: Union[int, _UNSET] = UNSET,
    rtc_region: Union[int, _UNSET] = UNSET,
    video_quality_mode: Union[int, _UNSET] = UNSET,
    default_auto_archive_duration: Union[int, _UNSET] = UNSET,
    *,
    reason: str = None,
) -> dict:
    route = Route("/channels/{channel_id}", channel_id=channel_id)
    params = http.get_params(
        name=name,
        type=type,
        position=position,
        topic=topic,
        nsfw=nsfw,
        rate_limit_per_user=rate_limit_per_user,
        bitrate=bitrate,
        user_limit=user_limit,
        permission_overwrites=permission_overwrites,
        parent_id=parent_id,
        rtc_region=rtc_region,
        video_quality_mode=video_quality_mode,
        default_auto_archive_duration=default_auto_archive_duration,
    )

    return await http.patch(route, json=params, reason=reason)


async def modify_thread_channel(
    http: RESTClient,
    channel_id: int,
    name: Union[str, _UNSET] = UNSET,
    archived: Union[bool, _UNSET] = UNSET,
    auto_archive_duration: Union[int, _UNSET] = UNSET,
    locked: Union[bool, _UNSET] = UNSET,
    invitable: Union[bool, _UNSET] = UNSET,
    rate_limit_per_user: Union[int, _UNSET] = UNSET,
    *,
    reason: str = None,
) -> dict:
    route = Route("/channels/{channel_id}", channel_id=channel_id)
    params = http.get_params(
        name=name,
        archived=archived,
        auto_archive_duration=auto_archive_duration,
        locked=locked,
        invitable=invitable,
        rate_limit_per_user=rate_limit_per_user,
    )

    return await http.patch(route, json=params, reason=reason)


async def delete_channel(
    http: RESTClient, channel_id: int, *, reason: str = None
) -> None:
    route = Route("/channels/{channel_id}", channel_id=channel_id)

    await http.delete(route, reason=reason, format="none")


async def get_channel_messages(
    http: RESTClient,
    channel_id: int,
    around: Union[int, _UNSET] = UNSET,
    before: Union[int, _UNSET] = UNSET,
    after: Union[int, _UNSET] = UNSET,
    limit: Union[int, _UNSET] = UNSET,
) -> list:
    route = Route("/channels/{channel_id}/messages", channel_id=channel_id)
    params = http.get_params(
        around=around,
        before=before,
        after=after,
        limit=limit,
    )

    return await http.get(route, qparams=params)


async def get_channel_message(
    http: RESTClient, channel_id: int, message_id: int
) -> dict:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}",
        channel_id=channel_id,
        message_id=message_id,
    )

    return await http.get(route)


async def create_message(
    http: RESTClient,
    channel_id: int,
    content: Union[str, _UNSET] = UNSET,
    tts: Union[bool, _UNSET] = UNSET,
    file: Union[File, _UNSET] = UNSET,
    embeds: Union[list, _UNSET] = UNSET,
    allowed_mentions: Union[dict, _UNSET] = UNSET,
    message_reference: Union[dict, _UNSET] = UNSET,
    components: Union[list, _UNSET] = UNSET,
    sticker_ids: Union[list, _UNSET] = UNSET,
) -> dict:
    route = Route("/channels/{channel_id}/messages", channel_id=channel_id)
    params = http.get_params(
        content=content,
        tts=tts,
        embeds=embeds,
        allowed_mentions=allowed_mentions,
        message_reference=message_reference,
        components=components,
        sticker_ids=sticker_ids,
    )

    return await http.post(route, files=[file], json=params)


async def crosspost_message(http: RESTClient, channel_id: int, message_id: int) -> dict:
    route = Route("/channels/{channel_id}/messages/{message_id}/crosspost")

    return await http.post(route)


async def create_reaction(
    http: RESTClient, channel_id: int, message_id: int, emoji: str
) -> None:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
        channel_id=channel_id,
        message_id=message_id,
        emoji=quote(emoji),
    )

    await http.put(route, format="none")


async def delete_own_reaction(
    http: RESTClient, channel_id: int, message_id: int, emoji: str
) -> None:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
        channel_id=channel_id,
        message_id=message_id,
        emoji=quote(emoji),
    )

    await http.delete(route, format="none")


async def delete_user_reaction(
    http: RESTClient, channel_id: int, message_id: int, emoji: str, user_id: int
) -> None:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}",
        channel_id=channel_id,
        message_id=message_id,
        emoji=quote(emoji),
        user_id=user_id,
    )

    await http.delete(route, format="none")


async def get_reactions(
    http: RESTClient,
    channel_id: int,
    message_id: int,
    emoji: str,
    after: Union[int, _UNSET] = UNSET,
    limit: Union[int, _UNSET] = UNSET,
) -> list:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id=channel_id,
        message_id=message_id,
        emoji=quote(emoji),
    )
    params = http.get_params(after=after, limit=limit)

    return await http.get(route, qparams=params)


async def delete_all_reactions(
    http: RESTClient, channel_id: int, message_id: int
) -> None:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/reactions",
        channel_id=channel_id,
        message_id=message_id,
    )

    await http.delete(route, format="none")


async def delete_all_reactions_for_emoji(
    http: RESTClient, channel_id: int, message_id: int, emoji: str
) -> None:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id=channel_id,
        message_id=message_id,
        emoji=quote(emoji),
    )

    await http.delete(route, format="none")


async def edit_message(
    http: RESTClient,
    channel_id: int,
    message_id: int,
    content: Union[str, _UNSET] = UNSET,
    embeds: Union[list, _UNSET] = UNSET,
    flags: Union[int, _UNSET] = UNSET,
    file: Union[File, _UNSET] = UNSET,
    allowed_mentions: Union[dict, _UNSET] = UNSET,
    attachments: Union[list, _UNSET] = UNSET,
    components: Union[list, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}",
        channel_id=channel_id,
        message_id=message_id,
    )
    params = http.get_params(
        content=content,
        embeds=embeds,
        flags=flags,
        allowed_mentions=allowed_mentions,
        attachments=attachments,
        components=components,
    )

    return await http.patch(route, files=[file], json=params)


async def delete_message(
    http: RESTClient, channel_id: int, message_id: int, *, reason: str = None
) -> None:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}",
        channel_id=channel_id,
        message_id=message_id,
    )

    await http.delete(route, reason=reason, format="none")


async def bulk_delete_messages(
    http: RESTClient, channel_id: int, messages: list
) -> None:
    route = Route("/channels/{channel_id}/messages/bulk-delete", channel_id=channel_id)
    params = http.get_params(
        messages=messages,
    )

    await http.delete(route, json=params, format="none")


async def edit_channel_permissions(
    http: RESTClient,
    channel_id: int,
    overwrite_id: int,
    allow: str,
    deny: str,
    type: int,
    *,
    reason: str = None,
) -> None:
    route = Route(
        "/channels/{channel_id}/permissions/{overwrite_id}",
        channel_id=channel_id,
        overwrite_id=overwrite_id,
    )
    params = http.get_params(
        allow=allow,
        deny=deny,
        type=type,
    )

    await http.put(route, json=params, reason=reason, format="none")


async def get_channel_invites(http: RESTClient, channel_id: int) -> list:
    route = Route("/channels/{channel_id}/invites")

    return await http.get(route)


async def create_channel_invite(
    http: RESTClient,
    channel_id: int,
    max_age: Union[int, _UNSET] = UNSET,
    max_uses: Union[int, _UNSET] = UNSET,
    temporary: Union[bool, _UNSET] = UNSET,
    unique: Union[bool, _UNSET] = UNSET,
    target_type: Union[int, _UNSET] = UNSET,
    target_user_id: Union[int, _UNSET] = UNSET,
    target_application_id: Union[int, _UNSET] = UNSET,
    *,
    reason: str = None,
) -> dict:
    route = Route("/channels/{channel_id}/invites", channel_id=channel_id)
    params = http.get_params(
        max_age=max_age,
        max_uses=max_uses,
        temporary=temporary,
        unique=unique,
        target_type=target_type,
        target_user_id=target_user_id,
        target_application_id=target_application_id,
    )

    return await http.post(route, json=params, reason=reason)


async def delete_channel_permission(
    http: RESTClient, channel_id: int, overwrite_id: int, *, reason: str = None
) -> None:
    route = Route(
        "/channels/{channel_id}/permissions/{overwrite_id}",
        channel_id=channel_id,
        overwrite_id=overwrite_id,
    )

    await http.delete(route, reason=reason, format="none")


async def follow_news_channel(
    http: RESTClient, channel_id: int, webhook_channel_id: int
) -> dict:
    route = Route("/channels/{channel_id}/followers", channel_id=channel_id)
    params = http.get_params(
        webhook_channel_id=webhook_channel_id,
    )

    return await http.post(route, json=params)


async def trigger_typing_indicator(http: RESTClient, channel_id: int) -> None:
    route = Route("/channels/{channel_id}/typing", channel_id=channel_id)

    await http.post(route, format="none")


async def get_pinned_messages(http: RESTClient, channel_id: int) -> list:
    route = Route("/channels/{channel_id}/pins", channel_id=channel_id)

    return await http.get(route)


async def pin_message(
    http: RESTClient, channel_id: int, message_id: int, *, reason: str = None
) -> None:
    route = Route(
        "/channels/{channel_id}/pins/{message_id}",
        channel_id=channel_id,
        message_id=message_id,
    )

    await http.post(route, reason=reason, format="none")


async def unpin_message(
    http: RESTClient, channel_id: int, message_id: int, *, reason: str = None
) -> None:
    route = Route(
        "/channels/{channel_id}/pins/{message_id}",
        channel_id=channel_id,
        message_id=message_id,
    )

    await http.delete(route, reason=reason, format="none")


async def start_thread_with_message(
    http: RESTClient,
    channel_id: int,
    message_id: int,
    name: str,
    auto_archive_duration: int,
    *,
    reason: str = None,
) -> dict:
    route = Route(
        "/channels/{channel_id}/messages/{message_id}/threads",
        channel_id=channel_id,
        message_id=message_id,
    )
    params = http.get_params(
        name=name,
        auto_archive_duration=auto_archive_duration,
    )

    return await http.post(route, json=params, reason=reason)


async def start_thread_without_message(
    http: RESTClient,
    channel_id: int,
    name: str,
    auto_archive_duration: int,
    type: Union[int, _UNSET] = UNSET,
    invitable: Union[bool, _UNSET] = UNSET,
    *,
    reason: str = None,
) -> dict:
    route = Route("/channels/{channel_id}/threads", channel_id=channel_id)
    params = http.get_params(
        name=name,
        auto_archive_duration=auto_archive_duration,
        type=type,
        invitable=invitable,
    )

    return await http.post(route, json=params, reason=reason)


async def join_thread(http: RESTClient, channel_id: int) -> None:
    route = Route("/channels/{channel_id}/thread-members/@me", channel_id=channel_id)

    await http.put(route, format="none")


async def add_thread_member(http: RESTClient, channel_id: int, user_id: int) -> None:
    route = Route(
        "/channels/{channel_id}/thread-members/{user_id}",
        channel_id=channel_id,
        user_id=user_id,
    )

    await http.put(route, format="none")


async def leave_thread(http: RESTClient, channel_id: int) -> None:
    route = Route("/channels/{channel_id}/thread-members/@me", channel_id=channel_id)

    await http.delete(route, format="none")


async def remove_thread_member(http: RESTClient, channel_id: int, user_id: int) -> None:
    route = Route(
        "/channels/{channel_id}/thread-members/{user_id}",
        channel_id=channel_id,
        user_id=user_id,
    )

    await http.delete(route, format="none")


async def list_thread_members(http: RESTClient, channel_id: int) -> list:
    route = Route("/channels/{channel_id}/thread-members", channel_id=channel_id)

    return await http.get(route)


async def list_active_threads(http: RESTClient, channel_id: int) -> list:
    warn(
        "list_active_threads() is a deprecated method and will be removed with the release of the v10 API."
    )
    route = Route("/channels/{channel_id}/threads/active", channel_id=channel_id)

    return await http.get(route)


async def list_public_archived_threads(
    http: RESTClient,
    channel_id: Union[int, _UNSET] = UNSET,
    before: Union[str, _UNSET] = UNSET,
    limit: Union[int, _UNSET] = UNSET,
) -> list:
    route = Route(
        "/channels/{channel_id}/threads/archived/public", channel_id=channel_id
    )
    params = http.get_params(
        before=before,
        limit=limit,
    )

    return await http.get(route, qparams=params)


async def list_private_archived_threads(
    http: RESTClient,
    channel_id: Union[int, _UNSET] = UNSET,
    before: Union[str, _UNSET] = UNSET,
    limit: Union[int, _UNSET] = UNSET,
) -> list:
    route = Route(
        "/channels/{channel_id}/threads/archived/private", channel_id=channel_id
    )
    params = http.get_params(
        before=before,
        limit=limit,
    )

    return await http.get(route, qparams=params)


async def list_joined_private_archived_threads(
    http: RESTClient,
    channel_id: Union[int, _UNSET] = UNSET,
    before: Union[str, _UNSET] = UNSET,
    limit: Union[int, _UNSET] = UNSET,
) -> list:
    route = Route(
        "/channels/{channel_id}/users/@me/threads/archived/private",
        channel_id=channel_id,
    )
    params = http.get_params(
        before=before,
        limit=limit,
    )

    return await http.get(route, qparams=params)
