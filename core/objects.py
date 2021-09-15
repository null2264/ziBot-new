"""Collection of Object."""
from __future__ import annotations

import copy
import importlib
import sqlite3
from inspect import isclass
from typing import Dict, Iterable, Optional

import discord
from discord.ext import commands

from .app_command import ApplicationCommand, Slash, WrappedOptions


PRIVATE_CMDS = "/applications/{app}/guilds/{guild}/commands"
CMDS = "/applications/{app}/commands"


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.execute("pragma journal_mode=wal")
        self.execute("pragma foreign_keys=ON")
        self.isolation_level = None
        self.row_factory = sqlite3.Row


def _slash_from_module(path: str):
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
            and issubclass(command, (Slash,))
            and getattr(command, "__app_subcommand__", 0) <= 0
        ):
            actualCommands.append(command)
    return actualCommands


class AppBot(commands.Bot):
    """Subclass of `commands.Bot` that supports Application Commands."""

    def __init__(self, slashGuild: Optional[int] = None, **kwargs):
        super().__init__(**kwargs)
        self.slashGuild = slashGuild
        self._guildAppCmds: Dict[int, Dict[str, ApplicationCommand]] = {}
        self._appCmds: Dict[str, ApplicationCommand] = {}

    def loadApp(self, modules: Iterable[str]):
        for modulePath in modules:
            slash = _slash_from_module(modulePath)
            if not slash:
                continue
            for s in slash:
                if s._guilds:
                    for guild in s._guilds:
                        try:
                            self._guildAppCmds[guild][s._name] = s
                        except KeyError:
                            self._guildAppCmds[guild] = {s._name: s}
                else:
                    self._appCmds[s._name] = s

    async def registerSlash(self):
        """Register slash commands"""
        me: discord.ClientUser = self.user  # type: ignore

        fmt = [cmd._toDict() for cmd in self._appCmds.values()]

        r = discord.http.Route("PUT", CMDS, app=me.id)  # type: ignore

        await self.http.request(r, json=fmt)

        for guild, cmds in self._guildAppCmds.items():
            fmt = [cmd._toDict() for cmd in cmds.values()]
            r = discord.http.Route(  # type: ignore
                "PUT", PRIVATE_CMDS, app=me.id, guild=guild
            )

            await self.http.request(r, json=fmt)

    async def process_app_commands(self, interaction: discord.Interaction):
        data = interaction.data
        if not data:
            return

        dataOpts = data.get("options", [])

        # TODO: handle subcommand and subcommand group
        try:
            command: ApplicationCommand = self._appCmds.get(data["name"])  # type: ignore
            if not command:
                self._guildAppCmds[interaction.guild_id][data["name"]]  # type: ignore
        except KeyError:
            return await interaction.response.send_message(
                "Invalid command, slash command takes awhile to update. Please try again later",
                ephemeral=True,
            )
        else:
            # Try to get subcommand or subcommand group
            for c in dataOpts:
                if c["type"] > 2:
                    continue

                try:
                    command = command._subcommands[c["name"]]
                except KeyError:
                    raise ValueError("Failed to get subcommand") from None
                options = copy.deepcopy(command._options)
                dataOpts = c.get("options", {})

            # Deep copy options
            options = copy.deepcopy(command._options)

        resolved = data.get("resolved")

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

                _user = resolved["users"][userId]  # type: ignore
                try:
                    _member = resolved.get("members", {}).get(userId)  # type: ignore
                except KeyError:
                    options[optName].value = discord.User(
                        state=interaction._state, data=_user
                    )
                else:
                    _member["user"] = _user
                    options[optName].value = discord.Member(
                        data=_member,
                        guild=interaction.guild,  # type: ignore
                        state=interaction._state,
                    )
        return await command(WrappedOptions(options, bot=self), interaction)

    async def on_interaction(self, interaction: discord.Interaction):
        """Mainly used to handle slash command"""
        if interaction.type == discord.InteractionType.application_command:
            return await self.process_app_commands(interaction)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        await self.login(token)
        await self.registerSlash()
        await self.connect(reconnect=reconnect)
