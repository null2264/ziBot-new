"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from __future__ import annotations

import datetime as dt
import time
from typing import TYPE_CHECKING

import discord
import humanize
from discord.app_commands import locale_str as _
from discord.ext import commands

from ...core import checks
from ...core import commands as cmds
from ...core.context import Context
from ...core.embed import ZEmbed, ZEmbedBuilder
from ...core.errors import DefaultError
from ...core.menus import ZMenuPagesView
from ...utils import utcnow
from ...utils.format import cleanifyPrefix, formatDiscordDT
from ..timer._views import LinkView
from ._help import CustomHelp
from ._pages import PrefixesPageSource
from .subcogs import MetaCustomCommands


if TYPE_CHECKING:
    from ...core.bot import ziBot


class Meta(MetaCustomCommands):
    """Bot-related commands."""

    icon = "🤖"
    cc = True

    def __init__(self, bot: ziBot):
        super().__init__(bot)

        # Custom help command stuff
        # help command's attribute
        attributes = dict(
            name="help",
            aliases=("?",),
            usage="[category / command]",
            description="Get information of a command or category",
            help=(
                "\n\nYou can use `filters` flag to set priority.\n"
                "For example:\n`>help info filters: custom built-in`, "
                "will show custom commands first then built-in commands "
                "in **info** category\n`>help info filters: custom`, "
                "will **only** show custom commands in **info** category"
            ),
            extras=dict(
                example=(
                    "help info",
                    "? weather",
                    "help info filters: custom",
                ),
                flags={
                    ("filters", "filter", "filt"): (
                        "Filter command type (`custom` or `built-in`), also "
                        "work as priority system. (Only works on category)"
                    ),
                },
            ),
        )
        # Backup the old/original command incase this cog unloaded
        self._original_help_command = bot.help_command
        # Replace default help menu with custom one
        self.bot.help_command = CustomHelp(command_attrs=attributes)
        self.bot.help_command.cog = self

        # TODO: Retrieve from DB
        self.highlights = {
            807260318270619748: {"ziro": [186713080841895936, 740089661703192709]}
        }

    @cmds.command(name=_("source"), description=_("source-desc"), hybrid=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def source(self, ctx):
        await ctx.try_reply(_("source-message", link=self.bot.links["Source Code"]))

    @cmds.command(
        name=_("about"),
        aliases=("botinfo", "bi"),
        description=_("about-desc"),
        hybrid=True,
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def about(self, ctx: Context):
        # Z3R0 Banner
        f = discord.File("./assets/img/banner.png", filename="banner.png")

        e = ZEmbedBuilder(
            description=_(ctx.bot.description + "-extended", license=ctx.bot.license),
        )
        e.setAuthor(
            name=ctx.bot.requireUser().name,
            iconUrl=ctx.bot.requireUser().display_avatar.url,
        )
        e.setImage(url="attachment://banner.png")
        e.addField(name=_("about-author-title"), value=ctx.bot.author, inline=True)
        e.addField(
            name=_("about-library-title"),
            value="[`discord.py`](https://github.com/Rapptz/discord.py) - `v{}`".format(discord.__version__),
            inline=True,
        )
        e.addField(name=_("about-version-title"), value=ctx.bot.version, inline=True)
        view = discord.ui.View()
        for k, v in ctx.bot.links.items():
            if k and v:
                view.add_item(discord.ui.Button(label=k, url=v))
        await ctx.try_reply(
            file=f,
            embed=await e.build(ctx, autoGenerateDT=True, addRequester=True),
            view=view,
        )

    @cmds.command(name=_("stats"), description=_("stats-desc"), hybrid=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stats(self, ctx: Context):
        botUser: discord.ClientUser | None = ctx.bot.user
        if not botUser:
            return
        uptime = utcnow() - self.bot.uptime
        e = ZEmbedBuilder()
        e.setAuthor(name=_("stats-title", bot=botUser.name), iconUrl=botUser.display_avatar.url)
        e.addField(name=_("stats-uptime-title"), value=humanize.precisedelta(uptime))
        e.addField(
            name=await ctx.translate(_("stats-command-title")),
            value=await ctx.translate(
                _(
                    "stats-command",
                    commandCount=sum(self.bot.commandUsage.values()),
                    customCommand=self.bot.customCommandUsage,
                )
            ),
        )
        await ctx.try_reply(embed=await e.build(ctx, autoGenerateDT=True, addRequester=True))

    @commands.command(
        name="prefixes",
        description="Shortcut for `prefix ls` command",
        invoke_without_command=True,
        with_app_command=False,
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefixes(self, ctx):
        await ctx.try_invoke(self.prefList)

    @commands.group(
        aliases=("pref",),
        description="Manages bot's custom prefix",
        extras=dict(
            example=(
                "prefix add ?",
                "pref remove !",
            )
        ),
        invoke_without_command=True,
        with_app_command=False,
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefix(self, ctx):
        # Since this is for legacy (chatbox) command exec, I don't think I need
        # to hybrid this
        await ctx.try_invoke(self.prefList)

    @prefix.command(
        name="list",
        aliases=("ls",),
        description="Get all prefixes",
        exemple=("prefix ls", "pref list"),
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefList(self, ctx: Context):
        if not ctx.guild:
            raise DefaultError("Custom prefix for user is not yet implemented! Ping me to check my default prefixes")
        prefixes = await ctx.guild.getPrefixes()
        menu = ZMenuPagesView(ctx, source=PrefixesPageSource(ctx, ["placeholder"] * 2 + prefixes))
        await menu.start()

    @prefix.command(
        name="add",
        aliases=("+",),
        description="Add a custom prefix",
        help='\n\nTips: Wrap prefix with quotation mark (`" "`) to add spaces to your prefix.',
        extras=dict(
            example=("prefix add ?", 'prefix + "please do "', "pref + z!"),
            perms={
                "bot": None,
                "user": "Moderator Role or Manage Guild",
            },
        ),
    )
    @checks.is_mod()
    async def prefAdd(self, ctx: Context, *prefix: str):
        _prefix = " ".join(prefix).lstrip()
        if not _prefix:
            return await ctx.error(_("prefix-empty"))

        try:
            await ctx.requireGuild().addPrefix(_prefix)
            await ctx.success(title=_("prefix-added", prefix=cleanifyPrefix(self.bot, _prefix)))
        except Exception as exc:
            await ctx.error(str(exc))

    @prefix.command(
        name="remove",
        aliases=("-", "rm"),
        description="Remove a custom prefix",
        help='\n\nTips: Wrap prefix with quotation mark (`" "`) if the prefix has spaces.',
        extras=dict(
            example=("prefix rm ?", 'prefix - "please do "', "pref remove z!"),
            perms={
                "bot": None,
                "user": "Moderator Role or Manage Guild",
            },
        ),
    )
    @checks.is_mod()
    async def prefRm(self, ctx: Context, *prefix: str):
        _prefix = " ".join(prefix).lstrip()
        if not _prefix:
            return await ctx.error(_("prefix-empty"))

        try:
            await ctx.requireGuild().rmPrefix(_prefix.lstrip())
            await ctx.success(title=_("prefix-removed", prefix=cleanifyPrefix(self.bot, _prefix)))
        except Exception as exc:
            await ctx.error(str(exc))

    @cmds.command(name=_("ping"), aliases=("p",), description=_("ping-desc"), hybrid=True)
    async def ping(self, ctx):
        start = time.perf_counter()
        msgPing = 0
        if not ctx.bot.config.test:
            await ctx.typing()
            end = time.perf_counter()
            msgPing = (end - start) * 1000

        e = ZEmbedBuilder(title=_("ping-title"))

        botLatency = f"{round(self.bot.latency*1000)}ms" if not ctx.bot.config.test else "∞"

        e.addField(
            name=_("ping-websocket-title"),
            value=botLatency,
            inline=True,
        )

        e.addField(
            name=_("ping-typing-title"),
            value=f"{round(msgPing)}ms",
        )

        await ctx.try_reply(embed=await e.build(ctx, autoGenerateDT=True, addRequester=True))

    @cmds.command(name=_("invite"), description=_("invite-desc"), hybrid=True)
    async def invite(self, ctx: Context):
        clientId = self.bot.requireUser().id
        e = ZEmbedBuilder(
            title=_("invite-embed-title", botUser=self.bot.requireUser().name),
            description=_(
                "invite-embed-desc",
                urlAdmin=discord.utils.oauth_url(
                    clientId,
                    permissions=discord.Permissions(8),
                ),
                urlRec=discord.utils.oauth_url(
                    clientId,
                    permissions=discord.Permissions(4260883702),
                ),
            ),
        )
        await ctx.try_reply(embed=await e.build(ctx))

    @commands.group(aliases=("hl",))
    async def highlight(self, ctx):
        """Manage your highlight words

        When a highlight word/phrase is found, the bot will send you a private
        message with the message that triggered it along with contexts."""
        pass

    @highlight.command()
    async def add(self, ctx, *, text: str):
        """Add a new highlight word/phrase

        Note, highlight words/phrases are NOT case-sensitive!"""
        text = text.lower()

        # TODO: Actually add the text to highlights db
        await ctx.try_reply(text)

    @commands.Cog.listener("on_message")
    async def onHighlight(self, message: discord.Message):
        guild = message.guild
        if message.author.bot or not message.content or not guild:
            return

        channel = message.channel

        if not (guildHighlight := self.highlights.get(guild.id)):
            return

        for hl, owners in guildHighlight.items():
            if hl not in message.content.lower():
                continue

            # Getting context
            msgs: List[discord.Message] = [message]
            async for history in channel.history(limit=4, before=message.created_at):
                msgs.append(history)

            context = []
            for msg in msgs:
                tmp = f"[{formatDiscordDT(msg.created_at, 'T')}] {msg.author}: {msg.clean_content or '_Only contains embed(s)_'}"
                if msg == message:
                    tmp = f"** {tmp} **"
                context.append(tmp)
            context.reverse()

            view = LinkView(links=[("Jump to Source", message.jump_url)])
            e = ZEmbed(
                title=f"Keyword: `{hl}`",
                description="\n".join(context),
            )

            for owner in owners:
                # Prevent "self-highlight"
                if owner == message.author.id:
                    continue

                # Check if member sent a message 30 minutes prior
                if await channel.history(
                    after=utcnow() - dt.timedelta(minutes=30.0)
                ).get(author__id=owner):
                    continue

                user = guild.get_member(owner) or await guild.fetch_member(owner)
                if user:
                    await user.send(
                        "In {0.channel.mention} ({0.guild})".format(message),
                        embed=e,
                        view=view,
                    )
