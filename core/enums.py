from discord.enums import Enum


class Emojis:
    ok = "<:ok2_0:873464878982115360>"
    error = "<:error:783265883228340245>"
    loading = "<a:loading:776255339716673566>"
    first = "<:first:873473059837870131>"
    back = "<:back:873473128175636480>"
    next = "<:next:873471591642726400>"
    last = "<:last:873471805120208926>"
    stop = "<:stop:873474135941066762>"
    info = "<:info:783206485051441192>"


class ApplicationCommandType(Enum):
    chat_input = 1
    user = 2
    message = 3
