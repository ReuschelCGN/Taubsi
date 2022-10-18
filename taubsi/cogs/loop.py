from taubsi.utils.logging import log
from taubsi.taubsi_objects import tb
from discord.ext import tasks, commands

import json
import requests

class Loop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.big_loop.start()

    @tasks.loop(hours=12)   
    async def big_loop(self):
        tb.reload_pogodata()
        log.info("Reloaded PogoData")

        try:
            tb.localenames_en = requests.get("https://raw.githubusercontent.com/WatWowMap/pogo-translations/master/static/locales/en.json").json()
        except Exception:
            pass
        if not tb.localenames_en:
            log.info(f"Error while requesting english locals from pogo-translations.")
        try:
            tb.localenames_de = requests.get("https://raw.githubusercontent.com/WatWowMap/pogo-translations/master/static/locales/de.json").json()
        except Exception:
            pass
        if not tb.localenames_de:
            log.info(f"Error while requesting german locals from pogo-translations.")

async def setup(bot):
    await bot.add_cog(Loop(bot))
