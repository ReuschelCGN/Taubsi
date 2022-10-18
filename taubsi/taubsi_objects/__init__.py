import json
import discord
from pogodata import PogoData
from discord.ext import commands
from .queries import Queries
from .translator import Translator


class TaubsiVars:
    def __init__(self):
        with open("config/config.json") as f:
            self.config = json.load(f)

        intents = discord.Intents.all()
        self.bot = commands.Bot(command_prefix="!", case_insensitive=1, intents=intents)
        self.queries = Queries(self.config, self.config["db_dbname"])
        self.intern_queries = Queries(self.config, self.config["db_taubsiname"])

        translator_ = Translator(self.config.get("language", "german"))
        self.translate = translator_.translate
        self.reload_pogodata()
        try:
            self.localenames_en = requests.get("https://raw.githubusercontent.com/WatWowMap/pogo-translations/master/static/locales/en.json").json()
        except Exception:
            pass
        try:
            self.localenames_de = requests.get("https://raw.githubusercontent.com/WatWowMap/pogo-translations/master/static/locales/de.json").json()
        except Exception:
            pass

    def reload_pogodata(self):
        self.pogodata = PogoData(self.config.get("language", "german"))


tb = TaubsiVars()
