import json
from . import tb
from taubsi.cogs.raids.pogo import Gym


def _convert_path_sql(fence):
    sql_fence = []
    for lat, lon in fence:
        sql_fence.append(f"{lat} {lon}")
    sql_fence.append(f"{fence[0][0]} {fence[0][1]}")

    return "(" + ",".join(sql_fence) + ")"


async def load_servers():
    with open("config/servers.json", "r") as f:
        raw_servers = json.load(f)
    with open("config/geofence.json", "r") as f:
        raw_fences = json.load(f)

    tb.gyms = {}
    tb.friendcode_channels = []
    tb.team_choose_channels = []
    tb.setup_channels = []
    tb.welcome_channels = []
    tb.raid_channels = {}
    tb.info_channels = {}
    tb.guilds = []
    tb.guild_ids = []

    for settings in raw_servers:
        for fence in raw_fences:
            if fence["name"].lower() == settings["geofence"].lower():
                sql_fence = _convert_path_sql(fence["path"])
                break

        query = (
            f"select name, gym.gym_id, url, latitude, longitude "
            f"from gymdetails "
            f"left join gym on gym.gym_id = gymdetails.gym_id "
            f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({sql_fence})'), point(latitude, longitude))"
        )
        gyms = await tb.queries.execute(query, as_dict=True)
        
        gym_list = []
        for gym_data in gyms:
            gym_list.append(Gym(gym_data))
        tb.gyms[settings["id"]] = gym_list
        
        tb.friendcode_channels += settings["friendcodes_allowed"]
        tb.team_choose_channels += settings["team_choose"]
        tb.setup_channels += settings["setup"]
        tb.welcome_channels += settings["welcome"]

        for channel_settings in settings["raid_channels"]:
            tb.raid_channels[channel_settings["id"]] = channel_settings

        raw_info_channels = settings.get("info_channels", [])
        if len(raw_info_channels) > 0:
            tb.info_channels[settings["id"]] = raw_info_channels

        guild = await tb.bot.fetch_guild(settings["id"])
        tb.guilds.append(guild)
        tb.guild_ids.append(guild.id)
        
        

