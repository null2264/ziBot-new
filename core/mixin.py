from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Dict, Optional

import discord
from discord.ext.commands import Cog

from core.objects import Slash


if TYPE_CHECKING:
    from databases import Database

    from core.bot import ziBot


PRIVATE_CMDS = "/applications/{app}/guilds/{guild}/commands"


class CogMixin:
    """Mixin for Cogs/Exts."""

    def __init__(self, bot: ziBot) -> None:
        self.bot: ziBot = bot

    @property
    def db(self) -> Database:
        return self.bot.db


class SlashCog(CogMixin):
    __slash_commands__: Dict[str, Slash] = {}

    def __init_subclass__(cls):
        slashCmds = {}
        for key, value in reversed(cls.__dict__.items()):
            if isinstance(value, Slash):
                slashCmds[value.name] = value

        cls.__slash_commands__ = slashCmds

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self._slash = list(self.__slash_commands__.values())
        self.bot.loop.create_task(self.registerSlash())

    async def registerSlash(self):
        await self.bot.wait_until_ready()

        _commands = [
            {
                "name": command.name,
                "description": (
                    command.description or "This command is not documented yet"
                ),
            }
            for command in self._slash
        ]

        if not _commands:
            return

        me: discord.ClientUser = self.bot.user  # type: ignore

        r = discord.http.Route(  # type: ignore
            "PUT", PRIVATE_CMDS, app=me.id, guild=807260318270619748
        )

        await self.bot.http.request(r, json=_commands)

    async def process_slash(self, cmd, interaction: discord.Interaction):
        await cmd.callback(self, interaction)

    @Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data:
            return

        if interaction.type != discord.InteractionType.application_command:
            return

        cmd: Optional[Slash] = self.__slash_commands__.get(
            interaction.data["name"]  # type: ignore
        )
        if not cmd:
            raise RuntimeError("Command not found")

        await self.process_slash(cmd, interaction)
