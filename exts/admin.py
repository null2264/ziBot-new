import discord


from discord.ext import commands


class Admin(commands.Cog):
    """Admin-only commands to configure the bot."""
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Admin(bot))
