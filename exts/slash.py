from __future__ import annotations

from typing import Any, Literal

import discord

from core.app_command import Slash


class Animal(Slash, description="Get a random animal picture"):
    ...


@Animal.subcommand
class Cat(Animal, description="Get a random cat picture"):
    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer()
        req = await self._bot.session.get("https://thatcopy.pw/catapi/rest/")
        url = (await req.json())["url"]
        e = discord.Embed().set_image(url=url)
        return await interaction.followup.send(embed=e)


@Animal.subcommand
class Dog(Animal, description="Get a random dog picture"):
    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer()
        req = await self._bot.session.get("https://random.dog/woof.json")
        url = (await req.json())["url"]
        e = discord.Embed().set_image(url=url)
        return await interaction.followup.send(embed=e)


class Echo(Slash):
    message: str

    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.send_message(self.message)


__commands__ = (Animal, Echo)
