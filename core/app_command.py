"""My slash command implementation"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import discord


class Option:
    """Class for 'chat input' application commands' option"""

    pass


class ApplicationCommand:
    """Class for application commands."""

    __app_type__: int = 1
    __app_name__: str
    __app_description__: Optional[str]

    def __init_subclass__(cls, *, name: str = None, description: str = None):
        cls.__app_name__ = str(name or cls.__name__).lower()
        cls.__app_description__ = description

    def toDict(self) -> Dict[str, Any]:
        """Convert Slash object into dict.

        Useful when registering Slash to discord
        """
        return {
            "type": getattr(self, "type", self.__app_type__),
            "name": getattr(self, "name", self.__app_name__),
            "description": getattr(self, "description", self.__app_description__)
            or "No description",
        }


class Slash(ApplicationCommand):
    """Class for 'CHAT-INPUT' application commands.

    Planned usage:

    @slash(...)
    async def hello(self, interaction):
        await interaction.response.send_message("Hello World!")

    # or

    class Test(Slash):
        def callback(self, interaction):
            await interaction.response.send_message("テスト")
    """

    __app_type__: int = 1

    def __init__(self, **kwargs) -> None:
        self.type: int = self.__app_type__
        self.name: str = str(kwargs.get("name", self.__app_name__)).lower()
        self.description: Optional[str] = kwargs.get("description")

    async def callback(self, interaction: discord.Interaction) -> Any:
        pass

    async def __call__(self, *args, **kwargs) -> Any:
        return await self.callback(*args, **kwargs)


def slash(*, name: str = None):
    """Simple slash command without having to subclass it"""

    def decorator(func):
        ret = Slash(name=name or func.__name__)
        ret.callback = func
        return ret

    return decorator


@slash()
async def hello(interaction: discord.Interaction):
    return await interaction.response.send_message("Hello World")


class Test(Slash):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await asyncio.sleep(5)
        return await interaction.followup.send("テスト")
