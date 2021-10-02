from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from taubsi.cogs.setup.errors import *
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.core import log, Team
from taubsi.utils.checks import is_guild
from taubsi.utils.errors import command_error, TaubsiError

if TYPE_CHECKING:
    from taubsi.core import TaubsiBot


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self.max_level = 50

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, TaubsiError):
            log.exception(error)
            return
        await command_error(self.bot, ctx.message, error.__doc__, False)

    def __check_level(self, level):
        if level > self.max_level:
            raise LevelTooHigh
        if level <= 1:
            raise LevelTooSmall

    @staticmethod
    async def response(ctx, text):
        embed = discord.Embed(description=text, color=3092790)
        await ctx.send(embed=embed)

    @commands.command(aliases=["lvl", "l"])
    @commands.check(is_guild)
    async def level(self, ctx, level: int):
        self.__check_level(level)
        await self.response(ctx, self.bot.translate("setup_set_level").format(level))
        user = TaubsiUser()
        await user.from_command(ctx.author)
        user.level = level
        await user.update()

    @commands.command(aliases=["lvlup", "up"])
    @commands.check(is_guild)
    async def levelup(self, ctx):
        user = TaubsiUser()
        await user.from_command(ctx.author)

        level = user.level + 1
        self.__check_level(level)
        await self.response(ctx, self.bot.translate("setup_level_up").format(level))

        user.level = level
        await user.update()

    @commands.command(aliases=["n"])
    @commands.check(is_guild)
    async def name(self, ctx, *, name):
        await self.response(ctx, self.bot.translate("setup_name").format(name))
        user = TaubsiUser()
        await user.from_command(ctx.author)
        user.name = name
        await user.update()

    @commands.command(aliases=["code", "freund"])
    @commands.check(is_guild)
    async def trainercode(self, ctx, *, arg=None):
        member = None
        try:
            member = await commands.MemberConverter().convert(ctx, arg)
        except commands.CommandError:
            member = ctx.author
        
        user = TaubsiUser()
        await user.from_command(member)

        if member or arg is None:
            if not user.friendcode:
                raise NoCodeSet
            await ctx.send(f"`{user.friendcode}`")

        else:
            if isinstance(arg, str):
                try:
                    arg = int(arg.replace(" ", ""))
                except:
                    raise WrongCodeFormat
            user = TaubsiUser()
            await user.from_command(ctx.author)
            user.friendcode = int(arg)
            await user.update()
            await self.response(ctx, self.bot.translate("tb_saved_code"))

    @staticmethod
    def __team_aliases(team_name):
        aliases = {
            Team(1): ["mystic", "blau", "weisheit", "team_blau"],
            Team(2): ["valor", "rot", "wagemut", "team_rot"],
            Team(3): ["instinct", "gelb", "intuition", "team_gelb"]
        }
        for enum, alias in aliases.items():
            if [name for name in alias if name in team_name.lower()]:
                return enum
        return Team(0)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id not in self.bot.team_choose_ids:
            return
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        member = message.guild.get_member(payload.user_id)
        user = TaubsiUser()
        await user.from_command(member)
        user.team = self.__team_aliases(payload.emoji.name)
        await user.update()
    
    @commands.command()
    @commands.check(is_guild)
    async def team(self, ctx, team_name):
        user = TaubsiUser()
        await user.from_command(ctx.author)
        team = self.__team_aliases(team_name)
        if team.value == 0:
            raise NoTeam
        user.team = team
        await user.update()
        await self.response(ctx, self.bot.translate("setup_team").format(team.name.lower().capitalize()))


def setup(bot):
    bot.add_cog(Setup(bot))
