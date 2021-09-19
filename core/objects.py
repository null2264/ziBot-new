"""Collection of Object."""
from __future__ import annotations

import copy
import importlib
import sqlite3
from inspect import isclass
from typing import Dict, Iterable, Optional, Union

import discord
from discord.ext import commands

from .app_command import (
    ApplicationCommand,
    MessageCommand,
    Slash,
    UserCommand,
    WrappedOptions,
    _command_to_dict,
)


PRIVATE_CMDS = "/applications/{app}/guilds/{guild}/commands"
CMDS = "/applications/{app}/commands"


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.execute("pragma journal_mode=wal")
        self.execute("pragma foreign_keys=ON")
        self.isolation_level = None
        self.row_factory = sqlite3.Row


def _slashFromModule(path: str):
    try:
        module = importlib.import_module(path)
    except ImportError:
        return None

    actualCommands = []
    commands = getattr(module, "__commands__", None)
    if not commands:
        commands = [getattr(module, name) for name in dir(module)]
    for command in commands:
        if (
            isclass(command)
            and issubclass(command, (Slash, UserCommand, MessageCommand))
            and getattr(command, "__app_subcommand__", 0) <= 0
        ):
            actualCommands.append(command)
    return actualCommands


def _userFromResolved(
    id, guild, state, resolved
) -> Union[discord.Member, discord.User]:
    _user = resolved["users"][id]
    try:
        _member = resolved["members"][id]
    except KeyError:
        return discord.User(data=_user, state=state)
    else:
        _member["user"] = _user
        return discord.Member(
            data=_member,
            guild=guild,
            state=state,
        )


def _messageFromResolved(id, channel, state, resolved) -> discord.Message:
    _message = resolved["messages"][id]
    return discord.Message(state=state, channel=channel, data=_message)


class AppBot(commands.Bot):
    """Subclass of `commands.Bot` that supports Application Commands."""

    def __init__(self, slashGuild: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.slashGuild = slashGuild
        self._guildAppCmds: Dict[int, Dict[str, ApplicationCommand]] = {}
        self._appCmds: Dict[str, ApplicationCommand] = {}

    def loadApp(self, modules: Iterable[str]):
        for modulePath in modules:
            slash = _slashFromModule(modulePath)
            if not slash:
                continue
            for s in slash:
                s = s()
                if s.__app_guilds__:
                    for guild in s.__app_guilds__:
                        try:
                            self._guildAppCmds[guild][s.__app_name__] = s
                        except KeyError:
                            self._guildAppCmds[guild] = {s.__app_name__: s}
                else:
                    self._appCmds[s.__app_name__] = s

    async def registerSlash(self):
        """Register slash commands"""
        me: discord.ClientUser = self.user  # type: ignore

        fmt = [_command_to_dict(cmd) for cmd in self._appCmds.values()]

        r = discord.http.Route("PUT", CMDS, app=me.id)  # type: ignore

        await self.http.request(r, json=fmt)

        for guild, cmds in self._guildAppCmds.items():
            fmt = [_command_to_dict(cmd) for cmd in cmds.values()]
            r = discord.http.Route(  # type: ignore
                "PUT", PRIVATE_CMDS, app=me.id, guild=guild
            )

            await self.http.request(r, json=fmt)

    def getAppCommand(
        self, name, guildId: Optional[int] = None
    ) -> Union[ApplicationCommand, Slash]:
        try:
            print(name)
            command = self._appCmds.get(name)  # type: ignore
            if not command and guildId is not None:
                command = self._guildAppCmds[guildId][name]  # type: ignore
            else:
                raise KeyError
        except KeyError:
            raise ValueError(
                "Invalid command, slash command takes awhile to update. Please try again later"
            ) from None
        return command

    async def process_app_commands(self, interaction: discord.Interaction):
        data = interaction.data
        if not data:
            return

        dataOpts = data.get("options", [])

        try:
            command = self.getAppCommand(data["name"], interaction.guild_id)
        except ValueError as err:
            return await interaction.response.send_message(
                str(err),
                ephemeral=True,
            )

        resolved = data.get("resolved")

        arg = None

        if isinstance(command, Slash):
            # Try to get subcommand or subcommand group
            for c in dataOpts:
                if c["type"] > 2:
                    continue

                try:
                    command = command.__app_subcommands__[c["name"]]
                except KeyError:
                    raise ValueError("Failed to get subcommand") from None
                options = copy.deepcopy(command.__app_options__)
                dataOpts = c.get("options", {})

            # Deep copy options
            options = copy.deepcopy(command.__app_options__)

            for s in dataOpts:
                optName = s["name"]

                if 3 <= s["type"] <= 5:
                    if (value := s.get("value")) is not None:
                        options[optName].value = value
                elif s["type"] == 6:
                    # Construct Member/User object out of resolved data
                    if not resolved:
                        continue

                    userId = s.get("value")
                    if not userId:
                        raise ValueError("Invalid User")

                    options[optName].value = _userFromResolved(
                        userId, interaction.guild, interaction._state, resolved
                    )
            arg = WrappedOptions(options, bot=self)
        elif isinstance(command, UserCommand):
            userId = data.get("target_id")
            if not userId:
                raise ValueError("Invalid User")

            arg = _userFromResolved(
                userId, interaction.guild, interaction._state, resolved
            )
        elif isinstance(command, MessageCommand):
            messageId = data.get("target_id")
            if not messageId:
                raise ValueError("Invalid Message")

            arg = _messageFromResolved(
                messageId, interaction.channel, interaction._state, resolved
            )
        return await command(interaction, arg)  # type: ignore

    async def on_interaction(self, interaction: discord.Interaction):
        """Mainly used to handle slash command"""
        print(interaction.data)
        if interaction.type == discord.InteractionType.application_command:
            return await self.process_app_commands(interaction)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.login(token)
        await self.registerSlash()
        await self.connect(reconnect=reconnect)
