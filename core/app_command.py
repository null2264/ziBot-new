"""My slash command implementation"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import discord
from discord.utils import MISSING


class Option:
    """Class for 'CHAT-INPUT' application commands' option"""

    def __init__(
        self,
        name: str,
        /,
        *,
        type: Any,
        description: Optional[str] = None,
        default: Any = MISSING,
    ) -> None:
        self.name: str = name
        self.type: Any = type
        self.description: Optional[str] = description
        self.default: Any = default

    @property
    def isRequired(self) -> bool:
        return self.default is MISSING

    def toDict(self) -> Dict[str, Any]:
        """Convert Slash object into dict.

        Useful when registering Slash to discord
        """
        return {
            "name": self.name,
            # TODO: Make a converter, to convert python type to discord app cmd type
            "type": 3,
            "description": self.description or "No description",
            "required": self.isRequired,
        }


class ApplicationCommand:
    """Class for application commands."""

    __app_type__: int = 1
    # NOTE: Name has to match `^[\w-]{1,32}$`
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

    # only for no argument and no subcommand slash
    @slash(...)
    async def hello(self, interaction):
        await interaction.response.send_message("Hello World!")

    # or

    class Test(Slash, name="test"):
        def __init__(self, **kwargs):
            super().__init__()
            options = [Option("channel", type=discord.Channel)]
            self.extendOptions(options)

        def callback(self, interaction):
            await interaction.response.send_message("テスト")
    """

    __app_type__: int = 1

    def __init__(self, **kwargs) -> None:
        self.type: int = self.__app_type__
        self.name: str = str(kwargs.get("name", self.__app_name__)).lower()
        self.description: Optional[str] = kwargs.get(
            "description", self.__app_description__
        )
        self._options: List[Option] = []

    @property
    def options(self):
        return self._options

    def extendOptions(self, options: List[Option]) -> None:
        self._options.extend(options)
        return

    def toDict(self) -> Dict[str, Any]:
        ret = super().toDict()
        ret["options"] = [opt.toDict() for opt in self.options]
        return ret

    async def callback(self, interaction: discord.Interaction) -> Any:
        pass

    async def __call__(self, *args, **kwargs) -> Any:
        return await self.callback(*args, **kwargs)


def slash(*, name: str = None, description: str = None):
    """Simple slash command without having to subclass it"""

    def decorator(func):
        ret = Slash(name=name or func.__name__, description=description)
        ret.callback = func
        return ret

    return decorator


@slash(description="Sends 'Hello World'")
async def hello(interaction: discord.Interaction):
    return await interaction.response.send_message("Hello World")


class Test(Slash):
    def __init__(self):
        super().__init__()
        self.extendOptions([Option("name", type=str)])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await asyncio.sleep(5)
        return await interaction.followup.send("テスト")
