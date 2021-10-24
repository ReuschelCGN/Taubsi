from typing import Dict, List, Optional, Any
import re

import requests

from taubsi.pogodata.pokemon import Pokemon, BaseStats
from taubsi.utils.utils import asyncget

GAMEMASTER_URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
PROTO_URL = "https://raw.githubusercontent.com/Furtif/POGOProtos/master/base/vbase.proto"
LOCALE_URL = "https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Texts/Latest%20APK/{}.txt"
REMOTE_LOCALE_URL = "https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Texts/Latest%20Remote/{}.txt"


class PogoData:
    base_stats: Dict[str, BaseStats] = {}
    mons: Dict[str, str] = {}
    forms: Dict[int, str] = {}
    moves: Dict[int, str] = {}

    def __init__(self, language: str, raw_protos: str, raw_gamemaster: List[dict]):
        mon_mapping = self._enum_to_dict(raw_protos, "HoloPokemonId")
        form_mapping = self._enum_to_dict(raw_protos, "Form")
        mega_mapping = self._enum_to_dict(raw_protos, "HoloTemporaryEvolutionId")

        for url in [LOCALE_URL, REMOTE_LOCALE_URL]:
            raw = requests.get(url.format(language.title())).text
            keys = re.findall(r"(?<=RESOURCE ID: ).*", raw)
            values = re.findall(r"(?<=TEXT: ).*", raw)

            for i in range(len(keys)):
                k: str = keys[i].strip("\r")
                v: str = values[i].strip("\r")
                if k.startswith("form_"):
                    form_name = k[5:]
                    form_id = form_mapping.get(form_name.upper())
                    if form_id:
                        self.forms[form_id] = v
                elif k.startswith("pokemon_name_"):
                    parts = k[13:].split("_")
                    if len(parts) == 2:
                        mega_id = int(parts[1])
                    else:
                        mega_id = 0
                    mon_id = int(parts[0])
                    self.mons[f"{mon_id}:0:{mega_id}"] = v
                elif k.startswith("move_name_"):
                    self.moves[int(k[10:])] = v

        result = []
        for entry in raw_gamemaster:
            templateid = entry.get("templateId", "")
            if re.search(r"^V\d{4}_POKEMON_", templateid):
                data = entry.get("data", {})
                settings = data.get("pokemonSettings", {})
                stats = settings.get("stats")
                if not settings or not stats:
                    continue
                mon = settings.get("pokemonId")
                mon_id = mon_mapping.get(mon, 0)
                form = settings.get("form")
                form_id = form_mapping.get(form, 0)
                base_stats = BaseStats(list(stats.values()))
                identifier = f"{mon_id}:{form_id}"
                self.base_stats[f"{identifier}:0"] = base_stats

                mega_overrides: Optional[List[dict]] = settings.get("tempEvoOverrides")
                if not mega_overrides:
                    continue
                for mega_override in mega_overrides:
                    stats = mega_override.get("stats")
                    if not stats:
                        continue
                    base_stats = BaseStats(list(stats.values()))
                    mega = mega_override.get("tempEvoId")
                    mega_id = mega_mapping.get(mega, 0)
                    self.base_stats[f"{identifier}:{mega_id}"] = base_stats

    @classmethod
    def make_sync(cls, language: str):
        raw_protos = requests.get(PROTO_URL).text
        raw_gamemaster = requests.get(GAMEMASTER_URL).json()
        return cls(language, raw_protos, raw_gamemaster)

    @classmethod
    async def make_async(cls, language: str):
        raw_protos = await asyncget(PROTO_URL, as_text=True)
        raw_gamemaster = await asyncget(GAMEMASTER_URL, as_json=True)
        return cls(language, raw_protos, raw_gamemaster)

    @staticmethod
    def _enum_to_dict(protos: str, enum: str) -> Dict[str, int]:
        proto = re.findall(f"enum {enum} " + r"{[^}]*}", protos, re.IGNORECASE)

        final = {}
        for entry in proto[0].split("\n"):
            if "}" in entry or "{" in entry:
                continue
            k: str = entry.split(" =")[0].strip()
            v: int = int(entry.split("= ")[1].split(";")[0].strip())
            final[k] = v

        return final

    def get_pokemon(self, data: Dict[str, Any]):
        return Pokemon.from_db(data, self)
