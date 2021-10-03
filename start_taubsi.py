from taubsi.core import bot
from taubsi.core.config_classes import Cog
from taubsi.cogs.raids.raid_commands import RaidCommand
from taubsi.cogs.playerstats.playerstats_commands import StatContext

bot.load_cogs()

for server in bot.servers:
    if Cog.RAIDS in bot.config.COGS:
        bot.add_application_command(command=RaidCommand, guild_id=server.id)
    if Cog.PLAYERSTATS in bot.config.COGS:
        bot.add_application_command(command=StatContext, guild_id=server.id)

bot.run(bot.config.BOT_TOKEN)
