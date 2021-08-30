"""Collection of Object."""
from __future__ import annotations

import sqlite3
from typing import Any, Optional

import discord


class Connection(sqlite3.Connection):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.execute("pragma journal_mode=wal")
        self.execute("pragma foreign_keys=ON")
        self.isolation_level = None
        self.row_factory = sqlite3.Row


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

    async def callback(self, interaction: discord.Interaction) -> Any:
        pass


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
