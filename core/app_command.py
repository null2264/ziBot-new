"""My slash command implementation"""
from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Union

import discord
from discord.utils import MISSING, resolve_annotation


@dataclass
class Choice:
    """Dataclass for 'CHAT-INPUT' application commands' choice"""

    name: str = MISSING
    value: Any = MISSING

    def _toDict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
        }

    def __str__(self) -> str:
        return self.value


@dataclass
class Option:
    """Dataclass for 'CHAT-INPUT' application commands' option"""

    name: str = MISSING
    description: Optional[str] = None
    annotation: Any = MISSING
    type: int = MISSING
    default: Any = MISSING
    options: List[Option] = MISSING
    value: Optional[Any] = None
    choices: List[Choice] = MISSING

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
        if self.choices is not MISSING:
            dict_["choices"] = [choice._toDict() for choice in self.choices]
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
                if (
                    annotation.__args__[-1] is type(None)  # noqa
                    and option.default is MISSING
                ):
                    # turn typing.Optional[type] into optional option
                    option.default = None
                    option.type = convertToType(annotation.__args__[0])
            elif origin is Literal:
                # "Limited" way to add choices
                _values = annotation.__args__
                t = type(_values[0])
                if t is bool:
                    t = int

                values = []
                for val in _values:
                    if type(val) is bool:
                        val = int(val)

                    if type(val) is not t:
                        raise TypeError("Choices can't have 2 different type!")

                    values.append(Choice(name=str(val), value=val))

                option.default = values[0]
                option.type = convertToType(t)
                option.choices = values
            else:
                raise TypeError(f"{origin} is not supported!")

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
        __app_subcommand__: int
        _subcommands: Dict[str, Any]

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
        if appType == 1:
            # `__app_subcommand__` values:
            # 0: ROOT
            # 1: SUB_COMMAND
            # 2: SUB_COMMAND_GROUP
            attrs["__app_subcommand__"] = 0
            attrs["_subcommands"] = {}

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
        options = []
        for option in list(self._options.values()) + list(
            getattr(self, "_subcommands", {}).values()
        ):
            if isinstance(option, Option):
                options.append(option._toDict())
            else:
                opt = option._toDict()
                opt["type"] = option.__app_subcommand__
                options.append(opt)
        return {
            "type": self._type,
            "name": self._name,
            "description": self._description or "No description",
            "options": options,
        }


class Slash(metaclass=ApplicationCommand):
    """Class for 'CHAT-INPUT' application commands.

    Planned usage:

    # inside `ext/slash.py`
    class Test(Slash, name=..., description=...):
        option1: str = Option("channel", default="What")
        option2: Optional[str]

        async def callback(self, interaction):
            await interaction.response.send_message(self.option1)

    class Animal(Slash, description="Get random animal pictures"):
        ...

    @Animal.subcommand(type=...)
    class Cat(Slash, description="Get random cat pictures"):
        async def callback(self, interaction):
            ...

    __commands__ = (Test,)  # Optional, but should faster if it's included

    # inside `main.py`
    bot = AppBot()
    bot.initSlash(modules=['ext.slash'])
    bot.run("TOKEN")
    """

    __app_type__: int = 1

    @classmethod
    def subcommand(cls, child, type: int = 1):
        if not getattr(cls, "_subcommands", False):
            cls._subcommands = {}

        def decorator(cls, child):
            child.__app_subcommand__ = type
            cls._subcommands[child._name] = child
            return child

        return decorator(cls, child)


class WrappedOptions:
    def __init__(self, options) -> None:
        self._options: Dict[str, Option] = options

    def __getattr__(self, option) -> Any:
        opt = self._options.get(option)
        if opt:
            return opt.value or opt.default
        return None
