"""Collection of Object."""
from __future__ import annotations

import copy
import sqlite3
from typing import Dict, Iterable

import discord
from discord.ext import commands

from .app_command import ApplicationCommand, WrappedOptions


PRIVATE_CMDS = "/applications/{app}/guilds/{guild}/commands"
CMDS = "/applications/{app}/commands"


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.execute("pragma journal_mode=wal")
        self.execute("pragma foreign_keys=ON")
        self.isolation_level = None
        self.row_factory = sqlite3.Row


class AppBot(commands.Bot):
    """Subclass of `commands.Bot` that supports Application Commands."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._slash: Dict[str, ApplicationCommand] = {}

    async def registerSlash(
        self, slashCmds: Iterable[ApplicationCommand], guildId: int = None
    ):
        """Register slash commands"""
        me: discord.ClientUser = self.user  # type: ignore

        fmt = []

        for slash in slashCmds:
            fmt.append(slash._toDict())

            self._slash[slash._name] = slash

        if guildId:
            r = discord.http.Route(  # type: ignore
                "PUT", PRIVATE_CMDS, app=me.id, guild=guildId
            )
        else:
            r = discord.http.Route("PUT", CMDS, app=me.id)  # type: ignore

        await self.http.request(r, json=fmt)

    async def process_app_commands(self, interaction: discord.Interaction):
        data = interaction.data
        if not data:
            return

        dataOpts = data.get("options", [])

        # TODO: handle subcommand and subcommand group
        try:
            command: ApplicationCommand = self._slash[interaction.data["name"]]  # type: ignore
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
        return await command(WrappedOptions(options), interaction)

    async def on_interaction(self, interaction: discord.Interaction):
        """Mainly used to handle slash command"""
        if interaction.type == discord.InteractionType.application_command:
            return await self.process_app_commands(interaction)
