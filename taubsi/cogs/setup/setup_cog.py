import discord
from discord.ext import commands
from taubsi.utils.logging import logging
from taubsi.cogs.setup.errors import *
from taubsi.taubsi_objects import tb
from taubsi.cogs.setup.objects import TaubsiUser
from config.emotes import *
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
        await self.reponse(ctx, tb.translate("setup_set_level").format(level))
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
        await self.reponse(ctx, tb.translate("setup_level_up").format(level))

        user.level = level
        await user.update()

    @commands.command(aliases=["n", "trainer"])
    @commands.check(is_guild)
    async def name(self, ctx, *, name):
        await self.reponse(ctx, tb.translate("setup_name").format(name))
        user = TaubsiUser()
        await user.from_command(ctx.author)
        user.name = name
        await user.update()

    @commands.command(aliases=["code", "freund", "friend"])
    @commands.check(is_guild)
    async def trainercode(self, ctx, *, arg):
        member = None
        try:
            member = await commands.MemberConverter().convert(ctx, arg)
        except:
            member = ctx.author

        user = TaubsiUser()
        await user.from_command(member)

        if member and arg == "anzeigen":
            if not user.friendcode:
                raise NoCodeSet
            await ctx.send(f"`{user.friendcode}`")

        else:
            if isinstance(arg, str) and arg != "anzeigen":
                try:
                    arg = str(arg.replace(" ", ""))
                except:
                    raise WrongCodeFormat
            if arg.isdigit():
                user = TaubsiUser()
                await user.from_command(ctx.author)
                user.friendcode = str(arg)
                await user.update()
                user.saved_code = tb.translate("setup_saved_code") + user.friendcode
            await self.reponse(ctx, user.saved_code)

    @commands.command(aliases=["einladen", "einladung", "inv", "invite", "invitation"])
    @commands.check(is_guild)
    async def invtrainercode(self, ctx):
        member = None
        try:
            member = await commands.MemberConverter().convert(ctx)
        except:
            member = ctx.author

        user = TaubsiUser()
        await user.from_command(member)

        if member:
            if not user.friendcode:
                raise NoCodeSet
            msg = await ctx.send(f"`{user.friendcode}`" + "  " + CONTROL_EMOJIS["invite"] + "  " + f"`{user.name}`")
            await msg.add_reaction("✅")
            await msg.add_reaction("⛔")

    def __team_aliases(self, team_name):
        aliases = {
            Team(1): ["mystic", "blau", "weisheit", "team_blau", "blue", "team_blue"],
            Team(2): ["valor", "rot", "wagemut", "team_rot", "red", "team_red"],
            Team(3): ["instinct", "gelb", "intuition", "team_gelb", "yellow", "team_yellow"]
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
        await self.reponse(ctx, tb.translate("setup_team").format(team.name.lower().capitalize()))

def setup(bot):
    bot.add_cog(Setup(bot))
