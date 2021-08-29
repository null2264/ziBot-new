"""Collection of Object."""
from __future__ import annotations

import sqlite3
from typing import Any

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

    class Hello(Slash, name="ping"):
        async def callback(self, interaction):
            await interaction.response.send_message("Hello World!")
    """

    def __init__(self, **kwargs) -> None:
        pass

    async def callback(self, interaction: discord.Interaction) -> Any:
        raise NotImplementedError
