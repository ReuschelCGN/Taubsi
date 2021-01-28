import re
from dateutil import tz

from taubsi.utils.logging import logging
from taubsi.utils.matcher import get_matches
from taubsi.utils.utils import reverse_get
from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.errors import *
from taubsi.cogs.raids.emotes import NUMBER_EMOJIS, CONTROL_EMOJIS
from taubsi.cogs.raids.objects import RaidMessage, BaseRaid, ChoiceMessage

import discord
import asyncio
import dateparser
import arrow
from discord.ext import tasks, commands

log = logging.getLogger("Raids")

class RaidCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.raidmessages = {}
        self.choicemessages = {}
        
        self.raid_loop.start()

    async def create_raid(self, raidmessage):
        self.raidmessages[raidmessage.message.id] = raidmessage

        emojis = []
        for number in range(1, 7):
            emojis.append(NUMBER_EMOJIS[number])
        emojis += list(CONTROL_EMOJIS.values())

        for emoji in emojis:
            await raidmessage.message.add_reaction(emoji)
        log.info(f"Created a raid at {raidmessage.gym.name}, {raidmessage.start_time}")

        await asyncio.sleep(60*5)
        await raidmessage.message.clear_reaction("❌")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel.id in tb.raid_channels.keys():
            return
        if message.author.id == self.bot.user.id:
            # creating a raid icon seperately from the raid message
            await asyncio.sleep(1)
            raidmessage = self.raidmessages.get(message.id)
            if raidmessage is not None:
                await asyncio.sleep(1)
                if raidmessage.embed.thumbnail.url == discord.Embed.Empty:
                    await raidmessage.set_image()
                    await raidmessage.edit_message()
            return
        
        log.info(f"Trying to create a Raid Message from {message.id}")

        channel_settings = tb.raid_channels[message.channel.id]

        possible_times = []
        for text in message.content.split(" "):
            times = re.split(":|\.|;|,", text)
            if [n for n in times if not n.isdigit()]:
                continue

            hour = str(times[0])
            minute = "00"
            if len(times) > 1:
                minute = str(times[1])
            time = dateparser.parse(f"{hour}:{minute}", languages=["de"])
            time = arrow.get(time, tz.tzlocal())
            possible_times.append((time, text))

        final_time = (None, "")
        gym_name_to_match = message.content

        if len(possible_times) == 1:
            final_time = possible_times[0]
        elif len(possible_times) > 1:
            for time, text in possible_times[::-1]:
                if (not channel_settings["is_event"]) and (not arrow.now().date() == time.date()):
                    continue
                if time > arrow.now():
                    final_time = (time, text)
                    break

        raid_start = final_time[0]
        gym_name_to_match = gym_name_to_match.replace(final_time[1], "")

        if raid_start is None:
            raise NoTime

        gym_names = get_matches([g.name for g in tb.gyms[message.guild.id]], gym_name_to_match, score_cutoff=0)

        def match_gym(gym_name):
            return [g for g in tb.gyms[message.guild.id] if g.name == gym_name][0]
        
        if len(gym_names) > 1:
            too_many_gyms = [match_gym(name) for name, _ in gym_names]
            choicemessage = ChoiceMessage(message, too_many_gyms, raid_start)
            choicemessage.make_embed()
            choicemessage.message = await message.channel.send(embed=choicemessage.embed)
            self.choicemessages[choicemessage.message.id] = choicemessage
            await choicemessage.react()
            return

        gym = match_gym(gym_names[0][0])

        raidmessage = RaidMessage()
        await raidmessage.from_command(gym, raid_start, message)
        await self.create_raid(raidmessage)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        raidmessage = self.raidmessages.get(payload.message_id)
        if raidmessage is not None:
            await raidmessage.add_reaction(payload)
            return
        choicemessage = self.choicemessages.get(payload.message_id)
        if choicemessage is not None:
            if payload.user_id == choicemessage.init_message.author.id:
                raidmessage = await choicemessage.reacted(payload)
                self.choicemessages.pop(payload.message_id)
                await self.create_raid(raidmessage)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        raidmessage = self.raidmessages.get(payload.message_id)
        if not raidmessage:
            return
        await raidmessage.remove_reaction(payload)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        raidmessage = self.raidmessages.get(message.id)
        if not raidmessage:
            return
        log.info(f"Gracefully deleting Raid at {raidmessage.gym.name}, {raidmessage.start_time}, {raidmessage.message_id}")
        await raidmessage.init_message.delete()
        await raidmessage.delete_role()
        self.raidmessages.pop(message.id)

    @tasks.loop(seconds=10)   
    async def raid_loop(self):
        """for channel_id in tb.raid_channels:
            channel = self.bot.get_channel(channel_id)
            messages = await channel.history(after=arrow.utcnow().shift(hours=-2).naive, oldest_first=False).flatten()
            for message in messages:
                if not message.author.id == self.bot.user.id:
                    continue
                raidmessage = self.raidmessages.get(message.id)
                if raidmessage is None:
                    continue
                if len(message.reactions) == 0:
                    continue"""
        
        raidmessages = self.raidmessages.copy().values()
        for raidmessage in raidmessages:
            try:
                message = raidmessage.message

                if arrow.utcnow() > raidmessage.start_time.shift(minutes=1):
                    log.info(f"Raid {raidmessage.message_id} started. Clearing reactions and deleting its role.")
                    await message.clear_reactions()
                    await raidmessage.delete_role()
                    self.raidmessages.pop(message.id)
                if arrow.utcnow() > raidmessage.start_time.shift(minutes=-5) and arrow.utcnow() < raidmessage.start_time.shift(minutes=-4):
                    if not raidmessage.notified_5_minutes:
                        await raidmessage.notify("‼️ Der Raid startet in 5 Minuten")
                        raidmessage.notified_5_minutes = True

                if isinstance(raidmessage.raid, BaseRaid) or not raidmessage.moves[0]:
                    updated_raid = await raidmessage.gym.get_active_raid(raidmessage.raid.level)
                    if updated_raid.compare != raidmessage.raid.compare:
                        log.info(f"Raid Boss at {raidmessage.message_id} changed. Updating")
                        if not raidmessage.raid.boss and updated_raid.boss:
                            await raidmessage.notify(f"🐣 Es ist ein {updated_raid.boss.name} geschlüpft")
                            await raidmessage.set_image()
                        raidmessage.raid = updated_raid
                        await raidmessage.make_base_embed()
                        await raidmessage.edit_message()
            except Exception as e:
                log.error("Error while Raid looping")
                log.exception(e)

def setup(bot):
    bot.add_cog(RaidCog(bot))