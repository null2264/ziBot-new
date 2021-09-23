from __future__ import annotations

from typing import Any, Literal

import discord

from core.app_command import MessageCommand, Slash, UserCommand


TESTING_GUILDS = [807260318270619748, 745481731133669476]


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


class Echo(Slash, guilds=TESTING_GUILDS):
    message: str

    async def callback(self, interaction: discord.Interaction, options) -> Any:
        await interaction.response.send_message(options.message)


class WhoIs(UserCommand, guilds=TESTING_GUILDS):
    async def callback(self, interaction: discord.Interaction, user) -> Any:
        await interaction.response.send_message(user.mention)


class MessageInfo(
    MessageCommand, name="Message Info", guilds=[807260318270619748, 745481731133669476]
):
    async def callback(self, inter, message: discord.Message):
        await inter.response.send_message(message.id)


class Which(Slash, guilds=TESTING_GUILDS):
    choices: Literal["hello", "test"]

    async def callback(self, interaction: discord.Interaction, options) -> Any:
        await interaction.response.send_message(f"Selected: {options.choices}")


__commands__ = (Animal, Echo, WhoIs, MessageInfo, Which)
