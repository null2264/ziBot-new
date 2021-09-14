from __future__ import annotations

from typing import Any, Literal

import discord

from core.app_command import Slash


class Test(Slash, description="test"):
    ...


@Test.subcommand
class Test2(Test):
    member: discord.Member

    async def callback(self, interaction: discord.Interaction) -> Any:
        return await interaction.response.send_message(self.member.mention)


@Test.subcommand
class Test3(Test):
    name: str = "Test"

    async def callback(self, interaction: discord.Interaction) -> Any:
        return await interaction.response.send_message(self.name)


class Echo(Slash):
    choices: Literal["test", "hello"]
    message: str = "Test"
    number: int = 1

    async def callback(self, interaction: discord.Interaction) -> Any:
        return await interaction.response.send_message(
            f"{self.message} {self.number} {self.choices}"
        )


# __commands__ = (Test, Echo)
