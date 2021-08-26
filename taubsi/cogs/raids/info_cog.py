from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.raidinfo import RaidInfo

import arrow
from discord.ext import tasks, commands

log = logging.getLogger("Raids")


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raid_infos = {}

        if tb.info_channels:
            gym_ids = []
            self.gyms = {}
            for guild_id in tb.info_channels.keys():
                for guild_gym in tb.gyms[guild_id]:
                    gym_ids.append("'" + guild_gym.id + "'")
                    self.gyms[guild_gym.id] = {
                        "gym": guild_gym,
                        "guild_id": guild_id
                    }

            self.query = (
                f"select gym_id, level, pokemon_id, form, costume, start, end, move_1, move_2, evolution "
                f"from raid "
                f"where end > utc_timestamp() and gym_id in ({','.join(gym_ids)}) "
                f"order by end asc "
            )
            self.info_loop.start()

    @tasks.loop(seconds=10)
    async def info_loop(self):
        result = await tb.queries.execute(self.query)

        for db_raid in result:
            try:
                raw_gym = self.gyms.get(db_raid[0], {})
                gym = raw_gym.get("gym")
                if gym is None:
                    continue

                guild_id = raw_gym["guild_id"]
                raidinfo = self.raid_infos.get(gym.id)

                if raidinfo is None:
                    raidinfo = await RaidInfo.from_db(gym, db_raid, tb.info_channels[guild_id])
                    if raidinfo:
                        self.raid_infos[gym.id] = raidinfo
                    continue

                if db_raid[2] is not None and not raidinfo.hatched:
                    await raidinfo.has_hatched(db_raid)
                    continue

            except Exception as e:
                log.error("Exception in RaidInfo Loop")
                log.exception(e)

        try:
            for raidinfo in list(self.raid_infos.values()):
                await raidinfo.update_buttons()
                if raidinfo.raid.end < arrow.utcnow():
                    await raidinfo.delete()
                    self.raid_infos.pop(raidinfo.gym.id)
        except Exception as e:
            log.error("Exception in RaidInfo Loop")
            log.exception(e)

    @info_loop.before_loop
    async def info_purge(self):
        for channel_settings in tb.info_channels.values():
            for channel_setting in channel_settings:
                channel = await tb.bot.fetch_channel(channel_setting["id"])
                await channel.purge(limit=1000)

def setup(bot):
    bot.add_cog(InfoCog(bot))