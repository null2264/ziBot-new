from __future__ import annotations

from typing import Any, Literal

import discord

from core.app_command import Slash, UserCommand


class Animal(Slash, description="Get a random animal picture"):
    ...


@Animal.subcommand
class Cat(Slash, description="Get a random cat picture"):
    async def callback(self, interaction: discord.Interaction, options) -> Any:
        await interaction.response.defer()
        req = await options._bot.session.get("https://thatcopy.pw/catapi/rest/")
        url = (await req.json())["url"]
        e = discord.Embed().set_image(url=url)
        return await interaction.followup.send(embed=e)


@Animal.subcommand
class Dog(Slash, description="Get a random dog picture"):
    async def callback(self, interaction: discord.Interaction, options) -> Any:
        await interaction.response.defer()
        req = await options._bot.session.get("https://random.dog/woof.json")
        url = (await req.json())["url"]
        e = discord.Embed().set_image(url=url)
        return await interaction.followup.send(embed=e)


class Echo(Slash, guilds=[807260318270619748, 745481731133669476]):
    message: str

    async def callback(self, interaction: discord.Interaction, options) -> Any:
        await interaction.response.send_message(options.message)


class Hello(UserCommand, guilds=[807260318270619748, 745481731133669476]):
    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.send_message("test")


class Member(Slash, guilds=[807260318270619748, 745481731133669476]):
    member: discord.Member

    async def callback(self, inter, opts):
        await inter.response.send_message(opts.member.mention)


__commands__ = (Animal, Echo, Hello, Member)
