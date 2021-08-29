"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import discord
from discord.ext import commands

from core.mixin import CogMixin


# guild_ids = [807260318270619748, 745481731133669476]


class SlashMeta(commands.Command):
    def __init__(self, func, **kwargs):
        self.isSlash = True
        super().__init__(func, **kwargs)


BASE_URL = "https://discord.com/api/v8"
CMDS = "/applications/{app}/commands"
CMD = "/applications/{app}/commands/{cmdId}"
PRIVATE_CMDS = "/applications/{app}/guilds/{guild}/commands"


class Slash(commands.Cog, CogMixin):
    """Slash commands handler."""

    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.bot.loop.create_task(self.registerSlash())

    async def registerSlash(self):
        await self.bot.wait_until_ready()

        _commands = [
            {
                "name": command.name,
                "description": (
                    command.help
                    or command.description
                    or command.brief
                    or "This command is not documented yet"
                ),
            }
            for command in self.get_commands()
            if getattr(command, "isSlash", False)
            and not isinstance(command, commands.Group)
        ]

        r = discord.http.Route(
            "PUT", PRIVATE_CMDS, app=self.bot.user.id, guild=807260318270619748
        )

        await self.bot.http.request(r, json=_commands)

    @commands.command(cls=SlashMeta, description="Just testing")
    async def slash_test(self, ctx):
        await ctx.send("test")

    @commands.Cog.listener("on_interaction")
    async def onExecuted(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.application_command:
            return

        print(interaction.data)
        await interaction.response.send_message(
            interaction.data["name"] + "\n[test](https://google.com)"
        )


def setup(bot):
    bot.add_cog(Slash(bot))
