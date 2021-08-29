from typing import Union

from ...utils import _UNSET, UNSET
from ..client import RESTClient
from ..route import Route


async def register_global_application_command(
    http: RESTClient,
    application_id: int,
    name: str,
    description: str,
    options: Union[list, _UNSET] = UNSET,
    default_permissions: Union[bool, _UNSET] = UNSET,
    type: Union[int, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/applications/commands/{application_id}/commands",
        application_id=application_id,
    )
    params = http.get_params(
        name=name,
        description=description,
        options=options,
        default_permissions=default_permissions,
        type=type,
    )

    return await http.post(route, json=params)


async def register_guild_application_command(
    http: RESTClient,
    application_id: int,
    guild_id: int,
    name: str,
    description: str,
    options: Union[list, _UNSET] = UNSET,
    default_permissions: Union[bool, _UNSET] = UNSET,
    type: Union[int, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/applications/commands/{application_id}/guilds/{guild_id}/commands",
        application_id=application_id,
        guild_id=guild_id,
    )
    params = http.get_params(
        name=name,
        description=description,
        options=options,
        default_permissions=default_permissions,
        type=type,
    )

    return await http.post(route, json=params)


async def delete_global_application_command(
    http: RESTClient, application_id: str, command_id: int
) -> None:
    route = Route(
        "/applications/{application_id}/commands/{command_id}",
        application_id=application_id,
        command_id=command_id,
    )

    await http.delete(route)


async def delete_guild_application_command(
    http: RESTClient, application_id: str, guild_id: int, command_id: int
) -> None:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
        application_id=application_id,
        guild_id=guild_id,
        command_id=command_id,
    )

    await http.delete(route)


async def get_global_application_command(
    http: RESTClient, application_id: int, command_id: int
) -> dict:
    route = Route(
        "/applications/{application_id}/commands/{command_id}",
        application_id=application_id,
        command_id=command_id,
    )

    return await http.get(route)


async def get_guild_application_command(
    http: RESTClient, application_id: int, guild_id: int, command_id: int
) -> dict:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
        application_id=application_id,
        guild_id=guild_id,
        command_id=command_id,
    )

    return await http.get(route)


async def edit_global_application_command(
    http: RESTClient,
    application_id: int,
    command_id: int,
    name: Union[str, _UNSET] = UNSET,
    description: Union[str, _UNSET] = UNSET,
    options: Union[list, _UNSET] = UNSET,
    default_permissions: Union[bool, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/applications/{application_id}/commands/{command_id}",
        application_id=application_id,
        command_id=command_id,
    )
    params = http.get_params(
        name=name,
        description=description,
        options=options,
        default_permissions=default_permissions,
    )

    return await http.post(route, json=params)


async def edit_guild_application_command(
    http: RESTClient,
    application_id: int,
    guild_id: int,
    command_id: int,
    name: Union[str, _UNSET] = UNSET,
    description: Union[str, _UNSET] = UNSET,
    options: Union[list, _UNSET] = UNSET,
    default_permissions: Union[bool, _UNSET] = UNSET,
) -> dict:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
        application_id=application_id,
        guild_id=guild_id,
        command_id=command_id,
    )
    params = http.get_params(
        name=name,
        description=description,
        options=options,
        default_permissions=default_permissions,
    )

    return await http.post(route, json=params)


async def bulk_overwrite_global_application_commands(
    http: RESTClient, application_id: int, commands: list
) -> list:
    route = Route(
        "/applications/{application_id}/commands", application_id=application_id
    )
    params = http.get_params(
        commands=commands,
    )

    return await http.put(route, json=params)


async def bulk_overwrite_guild_application_commands(
    http: RESTClient, application_id: int, guild_id: int, commands: list
) -> list:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands",
        application_id=application_id,
        guild_id=guild_id,
    )
    params = http.get_params(
        commands=commands,
    )

    return await http.put(route, json=params)


async def get_guild_application_command_permissions(
    http: RESTClient, application_id: int, guild_id: int
) -> list:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/permissions",
        application_id=application_id,
        guild_id=guild_id,
    )

    return await http.get(route)


async def get_application_command_permissions(
    http: RESTClient, application_id: int, guild_id: int, command_id: int
) -> list:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions",
        application_id=application_id,
        guild_id=guild_id,
        command_id=command_id,
    )

    return await http.get(route)


async def edit_application_permissions(
    http: RESTClient,
    application_id: int,
    guild_id: int,
    command_id: int,
    permissions: list,
) -> dict:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions",
        application_id=application_id,
        guild_id=guild_id,
        command_id=command_id,
    )
    params = http.get_params(
        permissions=permissions,
    )

    return await http.put(route, json=params)


async def batch_edit_application_permissions(
    http: RESTClient,
    application_id: int,
    guild_id: int,
    command_id: int,
    command_permissions: list,
) -> dict:
    route = Route(
        "/applications/{application_id}/guilds/{guild_id}/commands/permissions",
        application_id=application_id,
        guild_id=guild_id,
    )

    return await http.put(route, json=command_permissions)
