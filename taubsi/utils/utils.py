import aiohttp
from math import floor

def reverse_get(dict_, value):
    return list(dict_.keys())[list(dict_.values()).index(value)]

async def asyncget(url, as_json=False, as_text=False):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if as_json:
                return await resp.json()
            if as_text:
                return await resp.text()
            return await resp.read()

def calculate_cp(level, basestats, iv):
    multipliers = {
        10: 0.422500014305115,
        15: 0.517393946647644,
        20: 0.597400009632111,
        25: 0.667934000492096
    }

    multiplier = multipliers.get(level, 0.5)
    attack = basestats[0] + iv[0]
    defense = basestats[1] + iv[1]
    stamina = basestats[2] + iv[2]
    return floor((attack * defense**0.5 * stamina**0.5 * multiplier**2) / 10)
