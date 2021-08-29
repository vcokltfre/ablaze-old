from typing import List, Optional, Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..route import Route


async def create_guild(
    http: RESTClient,
    name: str,
    region: Union[str, _UNSET] = UNSET,
    icon: Union[str, _UNSET] = UNSET,
    verification_level: Union[int, _UNSET] = UNSET,
    default_message_notifications: Union[int, _UNSET] = UNSET,
    explicit_content_filter: Union[int, _UNSET] = UNSET,
    roles: Union[list, _UNSET] = UNSET,
    channels: Union[list, _UNSET] = UNSET,
    afk_timeout: Union[int, _UNSET] = UNSET,
    system_channel_flags: Union[int, _UNSET] = UNSET,
) -> dict:
    route = Route("/guilds")
    params = http.get_params(
        name=name,
        region=region,
        icon=icon,
        verification_level=verification_level,
        default_message_notifications=default_message_notifications,
        explicit_content_filter=explicit_content_filter,
        roles=roles,
        channels=channels,
        afk_timeout=afk_timeout,
        system_channel_flags=system_channel_flags,
    )

    return await http.post(route, json=params)


async def get_guild(http: RESTClient, guild_id: int, with_counts: bool) -> dict:
    route = Route("/guilds/{guild_id}", guild_id=guild_id)
    params = http.get_params(with_counts=with_counts)

    return await http.get(route, qparams=params)


async def get_guild_preview(http: RESTClient, guild_id: int) -> dict:
    route = Route("/guilds/{guild_id}/preview", guild_id=guild_id)

    return await http.get(route)


async def modify_guild(
    http: RESTClient,
    guild_id: int,
    name: Union[str, _UNSET] = UNSET,
    region: Union[str, _UNSET] = UNSET,
    verification_level: Union[int, _UNSET] = UNSET,
    default_message_notifications: Union[int, _UNSET] = UNSET,
    explicit_content_filter: Union[int, _UNSET] = UNSET,
    afk_channel_id: Union[int, _UNSET] = UNSET,
    afk_timeout: Union[int, _UNSET] = UNSET,
    icon: Union[str, _UNSET] = UNSET,
    owner_id: Union[int, _UNSET] = UNSET,
    splash: Union[str, _UNSET] = UNSET,
    discovery_splash: Union[str, _UNSET] = UNSET,
    banner: Union[str, _UNSET] = UNSET,
    system_channel_id: Union[int, _UNSET] = UNSET,
    system_channel_flags: Union[int, _UNSET] = UNSET,
    rules_channel_id: Union[int, _UNSET] = UNSET,
    public_updates_channel_id: Union[int, _UNSET] = UNSET,
    preferred_locale: Union[str, _UNSET] = UNSET,
    features: Union[list, _UNSET] = UNSET,
    description: Union[str, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route("/guilds/{guild_id}", guild_id=guild_id)
    params = http.get_params(
        name=name,
        region=region,
        verification_level=verification_level,
        default_message_notifications=default_message_notifications,
        explicit_content_filter=explicit_content_filter,
        afk_channel_id=afk_channel_id,
        afk_timeout=afk_timeout,
        icon=icon,
        owner_id=owner_id,
        splash=splash,
        discovery_splash=discovery_splash,
        banner=banner,
        system_channel_id=system_channel_id,
        system_channel_flags=system_channel_flags,
        rules_channel_id=rules_channel_id,
        public_updates_channel_id=public_updates_channel_id,
        preferred_locale=preferred_locale,
        features=features,
        description=description,
    )

    return await http.patch(route, json=params, reason=reason)


async def delete_guild(http: RESTClient, guild_id: int) -> None:
    route = Route("/guilds/{guild_id}", guild_id=guild_id)

    await http.delete(route, format="none")


async def get_guild_channels(http: RESTClient, guild_id: int) -> list:
    route = Route("/guilds/{guild_id}/channels", guild_id=guild_id)

    return await http.get(route)


async def create_guild_channel(
    http: RESTClient,
    guild_id: int,
    name: str,
    type: Union[int, _UNSET] = UNSET,
    topic: Union[str, _UNSET] = UNSET,
    bitrate: Union[int, _UNSET] = UNSET,
    user_limit: Union[int, _UNSET] = UNSET,
    rate_limit_per_user: Union[int, _UNSET] = UNSET,
    position: Union[int, _UNSET] = UNSET,
    permission_overwrites: Union[list, _UNSET] = UNSET,
    parent_id: Union[int, _UNSET] = UNSET,
    nsfw: Union[bool, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route("/guilds/{guild_id}/channels", guild_id=guild_id)
    params = http.get_params(
        name=name,
        type=type,
        topic=topic,
        bitrate=bitrate,
        user_limit=user_limit,
        rate_limit_per_user=rate_limit_per_user,
        position=position,
        permission_overwrites=permission_overwrites,
        parent_id=parent_id,
        nsfw=nsfw,
    )

    return await http.post(route, json=params, reason=reason)


async def modify_guild_channel_poisitions(
    http: RESTClient, guild_id: int, channels: list, *, reason: Optional[str] = None
) -> None:
    route = Route("/guilds/{guild_id}/channels", guild_id=guild_id)
    params = http.get_params(
        channels=channels,
    )

    await http.patch(route, json=params, reason=reason, format="none")


async def list_active_threads(http: RESTClient, guild_id: int) -> list:
    route = Route("/guilds/{guild_id}/threads/active", guild_id=guild_id)

    return await http.get(route)


async def get_guild_member(http: RESTClient, guild_id: int, user_id: int) -> dict:
    route = Route(
        "/guilds/{guild_id}/members/{user_id}", guild_id=guild_id, user_id=user_id
    )

    return await http.get(route)


async def list_guild_members(
    http: RESTClient,
    guild_id: int,
    limit: Union[int, _UNSET] = UNSET,
    after: Union[int, _UNSET] = UNSET,
) -> list:
    route = Route("/guilds/{guild_id}/members", guild_id=guild_id)
    params = http.get_params(
        limit=limit,
        after=after,
    )

    return await http.get(route, qparams=params)


async def search_guild_members(
    http: RESTClient, guild_id: int, query: str, limit: Union[int, _UNSET] = UNSET
) -> list:
    route = Route("/guilds/{guild_id}/members/search", guild_id=guild_id)
    params = http.get_params(
        query=query,
        limit=limit,
    )

    return await http.get(route, qparams=params)


async def modify_guild_member(
    http: RESTClient,
    guild_id: int,
    user_id: int,
    nick: Union[str, _UNSET] = UNSET,
    roles: Union[list, _UNSET] = UNSET,
    mute: Union[bool, _UNSET] = UNSET,
    deaf: Union[bool, _UNSET] = UNSET,
    channel_id: Union[int, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route(
        "/guilds/{guild_id}/members/{user_id}", guild_id=guild_id, user_id=user_id
    )
    params = http.get_params(
        nick=nick,
        roles=roles,
        mute=mute,
        deaf=deaf,
        channel_id=channel_id,
    )

    return await http.patch(route, json=params, reason=reason)


async def modify_current_user_nick(
    http: RESTClient,
    guild_id: int,
    nick: Optional[str] = None,
    *,
    reason: Optional[str] = None,
) -> str:
    route = Route("/guilds/{guild_id}/members/@me/nick", guild_id=guild_id)
    params = http.get_params(
        nick=nick,
    )

    return await http.patch(route, json=params, reason=reason)


async def add_guild_member_role(
    http: RESTClient,
    guild_id: int,
    user_id: int,
    role_id: int,
    *,
    reason: Optional[str] = None,
) -> None:
    route = Route(
        "/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
        guild_id=guild_id,
        user_id=user_id,
        role_id=role_id,
    )

    await http.put(route, reason=reason, format="none")


async def remove_guild_member_role(
    http: RESTClient,
    guild_id: int,
    user_id: int,
    role_id: int,
    *,
    reason: Optional[str] = None,
) -> None:
    route = Route(
        "/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
        guild_id=guild_id,
        user_id=user_id,
        role_id=role_id,
    )

    await http.delete(route, reason=reason, format="none")


async def remove_guild_member(
    http: RESTClient, guild_id: int, user_id: int, *, reason: Optional[str] = None
) -> None:
    route = Route(
        "/guilds/{guild_id}/members/{user_id}", guild_id=guild_id, user_id=user_id
    )

    await http.delete(route, reason=reason, format="none")


async def get_guild_bans(http: RESTClient, guild_id: int) -> list:
    route = Route("/guilds/{guild_id}/bans", guild_id=guild_id)

    return await http.get(route)


async def get_guild_ban(http: RESTClient, guild_id: int, user_id: int) -> dict:
    route = Route(
        "/guilds/{guild_id}/bans/{user_id}", guild_id=guild_id, user_id=user_id
    )

    return await http.get(route)


async def create_guild_ban(
    http: RESTClient, guild_id: int, user_id: int, *, reason: Optional[str] = None
) -> None:
    route = Route(
        "/guilds/{guild_id}/bans/{user_id}", guild_id=guild_id, user_id=user_id
    )

    await http.put(route, reason=reason, format="none")


async def remove_guild_ban(
    http: RESTClient, guild_id: int, user_id: int, *, reason: Optional[str] = None
) -> None:
    route = Route(
        "/guilds/{guild_id}/bans/{user_id}", guild_id=guild_id, user_id=user_id
    )

    await http.delete(route, reason=reason, format="none")


async def get_guild_roles(http: RESTClient, guild_id: int) -> list:
    route = Route("/guilds/{guild_id}/roles", guild_id=guild_id)

    return await http.get(route)


async def create_guild_role(
    http: RESTClient,
    guild_id: int,
    name: Union[str, _UNSET] = UNSET,
    permissions: Union[str, _UNSET] = UNSET,
    color: Union[int, _UNSET] = UNSET,
    hoist: Union[bool, _UNSET] = UNSET,
    mentionable: Union[bool, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route("/guilds/{guild_id}/roles", guild_id=guild_id)

    params = http.get_params(
        name=name,
        permissions=permissions,
        color=color,
        hoist=hoist,
        mentionable=mentionable,
    )
    return await http.post(route, json=params, reason=reason)


async def modify_guild_role_positions(
    http: RESTClient,
    guild_id: int,
    positions: list,
    *,
    reason: Optional[str] = None,
) -> list:
    route = Route("/guilds/{guild_id}/roles", guild_id=guild_id)

    return await http.patch(route, json=positions, reason=reason)


async def modify_guild_role(
    http: RESTClient,
    guild_id: int,
    role_id: int,
    name: Union[str, _UNSET] = UNSET,
    permissions: Union[str, _UNSET] = UNSET,
    color: Union[int, _UNSET] = UNSET,
    hoist: Union[bool, _UNSET] = UNSET,
    mentionable: Union[bool, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route(
        "/guilds/{guild_id}/roles/{role_id}", guild_id=guild_id, role_id=role_id
    )

    params = http.get_params(
        name=name,
        permissions=permissions,
        color=color,
        hoist=hoist,
        mentionable=mentionable,
    )

    return await http.patch(route, json=params, reason=reason)


async def delete_guild_role(
    http: RESTClient,
    guild_id: int,
    role_id: int,
    *,
    reason: Optional[str] = None,
) -> None:
    route = Route(
        "/guilds/{guild_id}/roles/{role_id}", guild_id=guild_id, role_id=role_id
    )

    await http.delete(route, format="none")


async def get_guild_prune_count(
    http: RESTClient,
    guild_id: int,
    days: Union[int, _UNSET] = UNSET,
    include_roles: Union[List[str], _UNSET] = UNSET,
) -> dict:
    if include_roles is not UNSET:
        include_roles = ",".join(include_roles)  # type: ignore

    route = Route("/guilds/{guild_id}/prune", guild_id=guild_id)

    params = http.get_params(
        days=days,
        include_roles=include_roles,
    )

    return await http.get(route, json=params)


async def begin_guild_prune(
    http: RESTClient,
    guild_id: int,
    days: Union[int, _UNSET] = UNSET,
    compute_prune_count: Union[bool, _UNSET] = UNSET,
    include_roles: Union[List[int], _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route("/guilds/{guild_id}/prune", guild_id=guild_id)

    params = http.get_params(
        days=days,
        compute_prune_count=compute_prune_count,
        include_roles=include_roles,
    )

    return await http.post(route, json=params, reason=reason)


async def get_guild_voice_regions(
    http: RESTClient,
    guild_id: int,
) -> list:
    route = Route("/guilds/{guild_id}/regions", guild_id=guild_id)

    return await http.get(route)


async def get_guild_invites(
    http: RESTClient,
    guild_id: int,
) -> list:
    route = Route("/guilds/{guild_id}/invites", guild_id=guild_id)

    return await http.get(route)


async def get_guild_integrations(
    http: RESTClient,
    guild_id: int,
) -> list:
    route = Route("/guilds/{guild_id}/integrations", guild_id=guild_id)

    return await http.get(route)


async def delete_guild_integration(
    http: RESTClient,
    guild_id: int,
    integration_id: int,
) -> None:
    route = Route(
        "/guilds/{guild_id}/integrations/{integration_id}",
        guild_id=guild_id,
        integration_id=integration_id,
    )

    await http.delete(route, format="none")


async def get_guild_widget_settings(
    http: RESTClient,
    guild_id: int,
) -> dict:
    route = Route("/guilds/{guild_id}/widget", guild_id=guild_id)

    return await http.get(route)


async def modify_guild_widget(
    http: RESTClient,
    guild_id: int,
    enabled: Union[bool, _UNSET] = UNSET,
    channel_id: Union[int, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route("/guilds/{guild_id}/widget", guild_id=guild_id)

    params = http.get_params(
        enabled=enabled,
        channel_id=channel_id,
    )

    return await http.patch(route, json=params, reason=reason)


async def get_guild_widget(
    http: RESTClient,
    guild_id: int,
) -> dict:
    route = Route("/guilds/{guild_id}/widget.json", guild_id=guild_id)

    return await http.get(route)


async def get_guild_vanity_url(
    http: RESTClient,
    guild_id: int,
) -> dict:
    route = Route("/guilds/{guild_id}/vanity-url", guild_id=guild_id)

    return await http.get(route)


async def get_guild_widget_image(
    http: RESTClient,
    guild_id: int,
    style: Union[str, _UNSET] = UNSET,
) -> bytes:
    route = Route("/guilds/{guild_id}/widget.png", guild_id=guild_id)

    params = http.get_params(style=style)

    return await http.get(route, qparams=params, format="bytes")


async def get_guild_welcome_screen(
    http: RESTClient,
    guild_id: int,
) -> dict:
    route = Route("/guilds/{guild_id}/welcome-screen", guild_id=guild_id)

    return await http.get(route)


async def modify_guild_welcome_screen(
    http: RESTClient,
    guild_id: int,
    enabled: Union[bool, _UNSET] = UNSET,
    welcome_channels: Union[List[dict], _UNSET] = UNSET,
    description: Union[str, _UNSET] = UNSET,
    *,
    reason: Optional[str] = None,
) -> dict:
    route = Route("/guilds/{guild_id}/welcome-screen", guild_id=guild_id)

    params = http.get_params(
        enabled=enabled,
        welcome_channels=welcome_channels,
        description=description,
    )

    return await http.patch(route, json=params, reason=reason)


async def modify_current_user_voice_state(
    http: RESTClient,
    guild_id: int,
    channel_id: int,
    suppress: Union[bool, _UNSET] = UNSET,
    request_to_speak_timestamp: Union[str, _UNSET] = UNSET,
) -> dict:
    route = Route("/guilds/{guild_id}/voice-states/@me", guild_id=guild_id)

    params = http.get_params(
        suppress=suppress,
        request_to_speak_timestamp=request_to_speak_timestamp,
    )

    return await http.patch(route, json=params)


async def modify_user_voice_state(
    http: RESTClient,
    guild_id: int,
    user_id: int,
    channel_id: int,
    suppress: bool,
):
    route = Route(
        "/guilds/{guild_id}/voice-states/{user_id}", guild_id=guild_id, user_id=user_id
    )

    params = http.get_params(
        channel_id=channel_id,
        suppress=suppress,
    )

    return await http.patch(route, json=params)
