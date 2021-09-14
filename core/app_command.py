"""My slash command implementation"""
from __future__ import annotations

import abc
import asyncio
import inspect
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Union

import discord
from discord.utils import MISSING, resolve_annotation


@dataclass
class Option:
    """Dataclass for 'CHAT-INPUT' application commands' option"""

    name: str = MISSING
    description: Optional[str] = None
    annotation: Any = MISSING
    type: int = MISSING
    default: Any = MISSING
    options: List[Option] = MISSING
    value: Any = MISSING

    @property
    def isRequired(self) -> bool:
        return self.default is MISSING

    def _toDict(self) -> Dict[str, Any]:
        dict_ = {
            "name": self.name,
            "description": self.description or "No description",
            "type": self.type,
            "required": self.isRequired,
        }
        if self.options is not MISSING:
            dict_["options"] = [option._toDict() for option in self.options]
        return dict_

    def copy(self):
        return Option(
            name=self.name,
            description=self.description,
            annotation=self.annotation,
            type=self.type,
            default=self.default,
            options=self.options,
            value=self.value,
        )


def option(
    *, name: str, default: Any = MISSING, options: List[Option] = MISSING
) -> Any:
    return Option(name=name, default=default, options=options)


def convertToType(typehint: type) -> int:
    return {  # type: ignore
        str: 3,
        int: 4,
        bool: 5,
        discord.Member: 6,
        discord.User: 6,
        discord.TextChannel: 7,
        discord.DMChannel: 7,
        discord.GroupChannel: 7,
        discord.CategoryChannel: 7,
        discord.Role: 8,
        (discord.User, discord.Role): 9,
        (discord.Member, discord.Role): 9,
        float: 10,
    }.get(typehint, 3)


def getOptions(
    namespace: Dict[str, Any], globals: Dict[str, Any], locals: Dict[str, Any]
) -> Dict[str, Option]:
    annotations = namespace.get("__annotations__", {})
    options: Dict[str, Option] = {}
    cache: Dict[str, Any] = {}
    names: Set[str] = set()
    for name, annotation in annotations.items():
        option = namespace.pop(name, MISSING)
        if isinstance(option, Option):
            option.annotation = annotation
        else:
            option = Option(name=name, annotation=annotation, default=option)

        if option.name is MISSING:
            option.name = name

        option.name = option.name.lower()

        annotation = option.annotation = resolve_annotation(
            option.annotation, globals, locals, cache
        )

        try:
            origin = annotation.__origin__
        except AttributeError:
            # A regular type hint
            option.type = convertToType(annotation)
        else:
            if origin is Union:
                if annotation.__args__[-1] is type(None) and option.default is MISSING:
                    option.default = None
                    option.type = convertToType(annotation.__args__[0])
            elif origin is Literal:
                print(origin)

        if option.type is MISSING:
            option.type = convertToType(annotation)

        name = option.name.lower()
        if name in names:
            raise TypeError(f"{option.name!r} option conflicts with previous option.")
        else:
            names.add(name)

        options[option.name] = option
    return options


class ApplicationCommand(type):
    if TYPE_CHECKING:
        __app_type__: int
        __app_name__: str
        __app_description__: Optional[str]
        __app_options__: Dict[str, Option]

    def __new__(
        cls: type,
        className: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        try:
            global_ns = sys.modules[attrs["__module__"]].__dict__
        except KeyError:
            global_ns = {}

        frame = inspect.currentframe()
        try:
            if frame is None:
                local_ns = {}
            else:
                if frame.f_back is None:
                    local_ns = frame.f_locals
                else:
                    local_ns = frame.f_back.f_locals
        finally:
            del frame

        options = {}
        for optionName, option in getOptions(attrs, global_ns, local_ns).items():
            options[optionName] = option

        # If type is not specified, assume its a slash command
        appType = attrs["__app_type__"] = attrs.get("__app_type__", 1)

        appName = name or className
        attrs["__app_name__"] = appName.lower() if appType == 1 else appName
        attrs["__app_description__"] = description
        attrs["__app_options__"] = options

        return type.__new__(cls, className, bases, attrs)  # type: ignore

    async def __call__(self, *args) -> Any:
        return await self.callback(*args)

    async def callback(self, interaction: discord.Interaction) -> Any:
        pass

    @property
    def _name(self) -> str:
        return self.__app_name__

    @property
    def _description(self) -> Optional[str]:
        return self.__app_description__

    @property
    def _options(self) -> Dict[str, Option]:
        return self.__app_options__

    @property
    def _type(self) -> int:
        return self.__app_type__

    def _toDict(self) -> Dict[str, Any]:
        """Convert Slash object into dict.

        Useful when registering Slash to discord
        """
        return {
            "type": self._type,
            "name": self._name,
            "description": self._description or "No description",
            "options": [option._toDict() for option in list(self._options.values())],
        }


class Slash(metaclass=ApplicationCommand):
    """Class for 'CHAT-INPUT' application commands.

    Planned usage:

    class Test(Slash, name="test"):
        option1: str = Option("channel", default="What")
        option2: Optional[str]

        def callback(self, interaction, options):
            await interaction.response.send_message(options.option1)
    """

    __app_type__: int = 1


class WrappedOptions:
    def __init__(self, options) -> None:
        self._options: Dict[str, Option] = options

    def __getattr__(self, option) -> Any:
        opt = self._options.get(option)
        if opt:
            if not opt.isRequired and opt.value is MISSING:
                return opt.default
            return opt.value
        return None


class Test(Slash, description="test"):
    member: discord.Member

    async def callback(self, interaction: discord.Interaction) -> Any:
        return await interaction.response.send_message(self.member.mention)


class Echo(Slash):
    message: str = "Test"
    number: int = 1

    async def callback(self, interaction: discord.Interaction) -> Any:
        return await interaction.response.send_message(f"{self.message} {self.number}")
