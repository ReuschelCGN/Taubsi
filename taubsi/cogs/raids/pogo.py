from __future__ import annotations
import random
from io import BytesIO
from typing import Union

import discord
import arrow
import json
import requests
from PIL import Image, ImageDraw
from pogodata.objects import Move
from pogodata.pokemon import Pokemon

from taubsi.utils.utils import asyncget, calculate_cp
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb

log = logging.getLogger("Raids")


class Gym:
    def __init__(self, id_: int = 0, name: str = "?", img: str = "", lat: float = 0, lon: float = 0):
        self.id = id_
        self.name = name
        self.img = img
        self.lat = lat
        self.lon = lon

        self.active_raid = None

    async def get_active_raid(self, level: int) -> Union[BaseRaid, ScannedRaid]:
        with open("config/config.json") as f:
            self.config = json.load(f)
        if (self.config["scanner"] == "rdm"):
            query = (
                f"select raid_level as level, raid_pokemon_id as pokemon_id, raid_pokemon_form as form, raid_pokemon_costume as costume, "
                f"raid_battle_timestamp as start, raid_end_timestamp as end, raid_pokemon_move_1 as move_1, raid_pokemon_move_2 as move_2, "
                f"raid_pokemon_evolution as evolution "
                f"from gym "
                f"where id = '{self.id}'"
            )
        else:
            query = (
                f"select level, pokemon_id, form, costume, start, end, move_1, move_2, evolution "
                f"from raid "
                f"where gym_id = '{self.id}'"
            )
        result = await tb.queries.execute(query)
        db_level, mon_id, form, costume, start, end, move_1, move_2, evolution = result[0]
        if (self.config["scanner"] == "rdm"):
            if start is None:
                start = arrow.utcnow()
        start = arrow.get(start)
        end = arrow.get(end)

        if end > arrow.utcnow() and db_level == level:
            if mon_id and mon_id > 0:
                mon = tb.pogodata.get_mon(id=mon_id, form=form, costume=costume, temp_evolution_id=evolution)
                move1 = tb.pogodata.get_move(id=move_1)
                move2 = tb.pogodata.get_move(id=move_2)
            else:
                mon = None
                move1 = None
                move2 = None
            return ScannedRaid(self, move1, move2, start, end, mon, level)

        return BaseRaid(self, level)


class BaseRaid:
    def __init__(self, gym: Gym, level: int = 5):
        self.level = level
        self.gym = gym

        self.cp20 = 0
        self.cp25 = 0
        self.boss = None
        self.name = "?"
        self.form = None
        self.pokebattler_name = "UNOWN"

        self.egg_url = ""
        self.boss_url = ""
        
        with open("config/config.json") as f:
            self.config = json.load(f)
        if self.config["uicon_repo"]:
            self.uicon_repo = self.config["uicon_repo"]
        else:
            self.uicon_repo = "https://raw.githubusercontent.com/nileplumb/PkmnHomeIcons/master/UICONS"

        if self.config["language"] == "english":
            self.localenames = tb.localenames_en
        else:
            self.localenames = tb.localenames_de

        available_bosses = tb.pogodata.raids[level]
        boss = None
        if len(available_bosses) == 1:
            boss = available_bosses[0]
        self.make_boss(boss)

    def make_boss(self, boss=None):
        if boss:
            self.boss = boss

            try:
                self.formname = self.localenames[f"form_{self.boss.form}"]
            except KeyError:
                self.formname = None
                log.info(f"Formname for Boss {self.boss} f{self.boss.form} missing!")

            if self.boss.form > 0 and self.formname != "Normal" and self.formname is not None:
                self.name = f"{self.boss.name} {self.formname}"
            else:
                self.name = self.boss.name

            self.pokebattler_name = self.boss.base_template
            if self.boss.temp_evolution_id > 0:
                self.pokebattler_name += "_MEGA"

            if boss.temp_evolution_id > 0:
                stats = tb.pogodata.get_mon(template=self.boss.base_template).stats
            else:
                stats = self.boss.stats
            self.cp20 = calculate_cp(20, stats, [15, 15, 15])
            self.cp25 = calculate_cp(25, stats, [15, 15, 15])
        else:
            if (self.level == 6):
                self.name = f"Mega {tb.translate('Egg')} 🥚"
            elif (self.level == 7):
                self.name = f"{tb.translate('legendary')} Mega {tb.translate('Egg')} 🥚"
            elif (self.level == 8):
                self.name = f"{tb.translate('ultra_wormhole_opend')} 🌀"
            elif (self.level == 9):
                self.name = f"{tb.translate('elite')} {tb.translate('Egg')} ⚡🥚"
            elif (self.level == 10):
                self.name = f"{tb.translate('primal')} {tb.translate('Egg')} ⚡🥚"
            elif ((self.level < 6) or (self.level > 10)):
                self.name = f"Level {self.level} {tb.translate('Egg')} 🥚"

        self.egg_url = (
            f"{self.uicon_repo}/raid/egg/{self.level}.png"
        )

        if self.boss:
            self.boss_url = (
                f"{self.uicon_repo}/pokemon/{self.boss.id}.png"
            )

            # MONFORMS ICON WHEN FORM AND NOT NORMAL
            try:
                self.formname = self.localenames[f"form_{self.boss.form}"]
            except KeyError:
                self.formname = "na"
            if self.boss.form > 0 and not self.formname.startswith("Normal") and not self.formname == "na":
                self.boss_url = (
                    f"{self.uicon_repo}/pokemon/{self.boss.id}_f{self.boss.form}.png"
                )
            else:
                self.boss_url = (
                    f"{self.uicon_repo}/pokemon/{self.boss.id}.png"
                )

            # MEGAMONS ICON
            if self.boss.temp_evolution_id == 1:
                self.boss_url = (
                    f"{self.uicon_repo}/pokemon/{self.boss.id}_e{self.boss.temp_evolution_id}.png"
                )

        else:
            self.boss_url = ""

    @property
    def compare(self):
        if self.boss:
            return str(self.boss.id) + "f" + str(self.boss.form) + "e" + str(self.boss.temp_evolution_id)
        else:
            return ""

    async def get_image(self):
        """
        Generate a circuar Gym Img with the boss in front of it.
        Similiar to how it'd show on the in-game nearby view.
        """
        if self.boss:
            mon_size = (105, 105)
            shiny = ""
            if random.randint(1, 30) == 20:
                # hotfix
                if self.boss.id not in (888, 889):
                    url = self.boss_url.replace(".png", "_s.png")
                else:
                    url = self.boss_url
            else:
                url = self.boss_url

            try:
                boss_result = await asyncget(url)
            except:
                boss_result = await asyncget(url.replace(shiny, ""))
        else:
            mon_size = (95, 95)
            boss_result = await asyncget(self.egg_url)
        log.info(f"Creating a Raid Icon for Gym {self.gym.name}")
        gym_result = await asyncget(self.gym.img)

        gymstream = BytesIO(gym_result)
        bossstream = BytesIO(boss_result)
        gym = Image.open(gymstream).convert("RGBA")

        # gym resizing
        size = min(gym.size)
        gym = gym.crop(((gym.width - size) // 2, (gym.height - size) // 2, (gym.width + size) // 2, (gym.height + size) // 2))

        mask = Image.new("L", (size*2, size*2), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size*2-2, size*2-2), fill=255)
        mask = mask.resize(gym.size, Image.ANTIALIAS)

        result = gym.copy()
        result.putalpha(mask)

        gym = result.resize((128, 128), Image.ANTIALIAS)
        bg = Image.new("RGBA", (150, 150), 0)
        bg.paste(gym)

        # boss resizing & combining
        mon = Image.open(bossstream).convert("RGBA")

        monbg = Image.new("RGBA", bg.size, 0)
        mon = mon.resize(mon_size, Image.ANTIALIAS)
        monbg.paste(mon, (bg.size[0]-mon.width, bg.size[1]-mon.height))

        final_img = Image.alpha_composite(bg, monbg)

        with BytesIO() as stream:
            final_img.save(stream, "PNG")
            stream.seek(0)
            image_msg = await tb.trash_channel.send(file=discord.File(stream, filename="raid-icon.png"))
            final_link = image_msg.attachments[0].url

        gymstream.close()
        bossstream.close()

        return final_link


class ScannedRaid(BaseRaid):
    def __init__(self, gym: Gym, move_1: Move, move_2: Move, start: arrow.Arrow, end: arrow.Arrow, mon: Pokemon,
                 level: int = 5):
        super().__init__(gym, level)
        self.moves = [move_1, move_2]
        self.start = start
        self.end = end

        if mon:
            self.make_boss(mon)

    @property
    def compare(self):
        compare = super().compare
        if self.moves[0]:
            return str(self.moves[0].id) + "-" + str(self.moves[1].id)
        else:
            return "s" + compare
