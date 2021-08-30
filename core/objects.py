"""Collection of Object."""
from __future__ import annotations

import sqlite3
from typing import Any, Optional


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

    class Cog(SlashCog):
        @slash_command()
        async def test(self, interaction):
            await interaction.response.send_message("Hello World!")
    """

    def __init__(self, func, **kwargs) -> None:
        self.name: str = kwargs["name"]
        self.description = None
        self._callback = func

    @property
    def callback(self) -> Any:
        return self._callback


def slash_command(*, cls=Slash, name: Optional[str] = None):
    def decorator(func):
        if isinstance(func, Slash):
            raise TypeError("Callback is already a slash command.")

        slash = Slash(func, name=name or func.__name__)

        return slash

    return decorator
