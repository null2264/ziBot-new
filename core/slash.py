"""My slash command implementation"""
from __future__ import annotations

from typing import Any, Dict, Optional

import discord


class Slash:
    """Class for slash commands.

    Planned usage:

    @slash(...)
    async def hello(self, interaction):
        await interaction.response.send_message("Hello World!")

    # or

    class Test(Slash):
        def callback(self, interaction):
            await interaction.response.send_message("テスト")
    """

    name: str = None  # type: ignore # just a placeholder
    description: Optional[str] = None

    def __init_subclass__(cls, *, name: str = None):
        cls.name = str(name or cls.__name__).lower()

    def __init__(self, **kwargs) -> None:
        if not kwargs:
            # only decorator use kwargs
            return

        self.name = str(kwargs.get("name", self.name)).lower()
        self.description = kwargs.get("description")

    def toDict(self) -> Dict[str, Any]:
        """Convert Slash object into dict.

        Useful when registering Slash to discord
        """
        return {"name": self.name, "description": self.description or "No description"}

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
        return await interaction.response.send_message("テスト")
