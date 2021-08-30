"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from core.context import Context
from core.mixin import SlashCog
from core.objects import slash_command


# guild_ids = [807260318270619748, 745481731133669476]


class SlashMeta(commands.Command):
    def __init__(self, func, **kwargs):
        self.isSlash = True
        super().__init__(func, **kwargs)


BASE_URL = "https://discord.com/api/v8"
CMDS = "/applications/{app}/commands"
CMD = "/applications/{app}/commands/{cmdId}"
PRIVATE_CMDS = "/applications/{app}/guilds/{guild}/commands"


class Slash(commands.Cog, SlashCog):
    """Slash commands handler."""

    @slash_command()
    async def slash_test(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await asyncio.sleep(5)
        e = discord.Embed(title="Test")
        msgContent = "test"
        return await interaction.followup.send(msgContent, embed=e)


def setup(bot):
    bot.add_cog(Slash(bot))
