from taubsi.taubsi_objects import tb
from taubsi.utils.logging import log
from taubsi.taubsi_objects.servers import load_servers

extensions = [
    "taubsi.cogs.raids.raid_cog",
    "taubsi.cogs.setup.setup_cog",
    "taubsi.cogs.loop",
    "taubsi.cogs.raids.info_cog"
]
startup = True


@tb.bot.event
async def on_ready():
    global startup

    if not startup:
        return
    await load_servers()
    tb.trash_channel = await tb.bot.fetch_channel(tb.config["trash_channel"])

    for extension in extensions:
        tb.bot.load_extension(extension)
    if tb.config.get("secret", False):
        tb.bot.load_extension("taubsi.cogs.setup.auto_setup_cog")
    raidcog = tb.bot.get_cog("RaidCog")
    await raidcog.final_init()
    
    log.info("Fully loaded, ready for action")
    startup = False

tb.bot.run(tb.config["bot_token"])
