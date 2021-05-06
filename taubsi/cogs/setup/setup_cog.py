import discord
from discord.ext import commands
from taubsi.utils.logging import logging
from taubsi.cogs.setup.errors import *
from taubsi.taubsi_objects import tb
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.utils.errors import command_error, TaubsiError
from taubsi.utils.checks import is_guild
from taubsi.utils.enums import Team

log = logging.getLogger("Setup")


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.max_level = 50

    async def cog_command_error(self, ctx, error):
        if not isinstance(error, TaubsiError):
            log.exception(error)
            return
        await command_error(ctx.message, error.__doc__, False)

    def __check_level(self, level):
        if level > self.max_level:
            raise LevelTooHigh
        if level <= 1:
            raise LevelTooSmall

    async def reponse(self, ctx, text):
        embed = discord.Embed(description=text, color=3092790)
        await ctx.send(embed=embed)

    @commands.command(aliases=["lvl", "l"])
    @commands.check(is_guild)
    async def level(self, ctx, level: int):
        self.__check_level(level)
        await self.reponse(ctx, f"✅ Du bist nun Level {level}")
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
        await self.reponse(ctx, f"🆙 Glückwunsch! Du bist nun Level {level}")

        user.level = level
        await user.update()

    @commands.command(aliases=["n"])
    @commands.check(is_guild)
    async def name(self, ctx, *, name):
        await self.reponse(ctx, f"✅ Dein Name ist jetzt {name}")
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
        except:
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
            await self.reponse(ctx, f"✅ Dein Trainercode ist nun gespeichert")

    def __team_aliases(self, team_name):
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
        if payload.channel_id in tb.team_choose_channels:
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
        await self.reponse(ctx, f"✅ Du bist jetzt in Team {team.name.lower().capitalize()}")

def setup(bot):
    bot.add_cog(Setup(bot))