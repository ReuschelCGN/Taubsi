from __future__ import annotations
from typing import NoReturn, List, Callable, Optional

import discord
import arrow

from math import floor

from taubsi.taubsi_objects import tb
from taubsi.cogs.raids.raidmessage import GMAPS_LINK, AMAPS_LINK, RaidMessage
from taubsi.cogs.raids.pogo import ScannedRaid, Gym


TIMEFORMAT_SHORT = tb.translate("timeformat_short")
TIMEFORMAT_LONG = tb.translate("timeformat_long")


class InfoTimeButton(discord.ui.Button):
    def __init__(self, raidinfo: RaidInfo, time: arrow.Arrow):
        self.time = time.to("local")
        label = self.time.strftime(TIMEFORMAT_SHORT)
        self.raidinfo = raidinfo

        super().__init__(style=discord.ButtonStyle.grey, label=label,
                         custom_id=str(self.raidinfo.gym.id) + "_" + label)

    async def callback(self, interaction: discord.Interaction) -> NoReturn:
        self.disabled = True
        await interaction.message.edit(embed=self.raidinfo.embed, view=self.view)
        await interaction.response.defer()

        if self.time < arrow.now().shift(minutes=4):
            return

        for channel_id in self.raidinfo.post_to:
            raidmessage = await RaidMessage.from_raidinfo(self.raidinfo.gym, self.raidinfo.raid, self.time,
                                                          interaction, channel_id)
            await self.raidinfo.create_raid(raidmessage)


class RaidInfoView(discord.ui.View):
    def __init__(self, raidinfo: RaidInfo):
        super().__init__(timeout=None)

        seconds_left = raidinfo.raid.end.int_timestamp - arrow.utcnow().int_timestamp
        if floor(seconds_left / 60) < 9:
            return

        if raidinfo.raid.start < arrow.utcnow():
            self.suggested_times = [arrow.utcnow().shift(minutes=5)]
        else:
            self.suggested_times = [raidinfo.raid.start]
        for time in arrow.Arrow.range("minute", raidinfo.raid.start, raidinfo.raid.end):
            if time.minute % 10 == 0 and \
                    self.suggested_times[-1].shift(minutes=5) < time < raidinfo.raid.end.shift(minutes=-6):
                self.suggested_times.append(time)

        for time in self.suggested_times:
            self.add_item(InfoTimeButton(raidinfo, time))


class RaidInfo:
    gym: Gym
    raid: ScannedRaid

    embed: discord.Embed
    messages: List[discord.Message]
    channels: List[discord.TextChannel]
    post_to: List[int]
    view: Optional[RaidInfoView]

    hatched: bool
    create_raid: Callable

    def __init__(self, gym: Gym):
        self.gym = gym
        raid_cog = tb.bot.get_cog("RaidCog")
        self.create_raid = raid_cog.create_raid

        self.embed = discord.Embed()
        self.messages = []
        self.channels = []
        self.post_to = []
        self.view = None
        self.hatched = False

    @classmethod
    async def from_db(cls, gym: Gym, db_raid, channel_settings) -> Optional[RaidInfo]:
        self = cls(gym)
        for channel_setting in channel_settings:
            if db_raid[1] not in channel_setting.get("levels", []):
                continue

            channel_id = channel_setting["id"]
            channel = await tb.bot.fetch_channel(channel_id)
            self.channels.append(channel)
            self.post_to += channel_setting.get("post_to", [])

        if not self.channels:
            return None

        self._make_raid(db_raid)
        self.make_embed()
        await self.send_message()

        return self

    def _make_raid(self, db_raid: tuple) -> NoReturn:
        gym_id, level, mon_id, form, costume, start, end, move_1, move_2, evolution = db_raid

        start = arrow.get(start)
        end = arrow.get(end)

        if mon_id is not None:
            self.hatched = True

        mon = tb.pogodata.get_mon(id=mon_id, form=form, costume=costume, temp_evolution_id=evolution)
        move1 = tb.pogodata.get_move(id=move_1)
        move2 = tb.pogodata.get_move(id=move_2)
        self.raid = ScannedRaid(self.gym, move1, move2, start, end, mon, level)
    
    async def has_hatched(self, db_raid: tuple) -> NoReturn:
        self._make_raid(db_raid)
        self.make_embed()
        await self.edit_message()

    def make_embed(self) -> NoReturn:
        formatted_end = self.raid.end.to("local").strftime(TIMEFORMAT_LONG)
        self.embed.title = self.raid.name

        if self.hatched:
            self.embed.title += " " + tb.translate("Raid")

            self.embed.description = (
                f"{tb.translate('Bis')} **{formatted_end}** <t:{self.raid.end.int_timestamp}:R>\n"
                f"100%: **{self.raid.cp20}** | **{self.raid.cp25}**\n"
                f"{tb.translate('Moves')}: " + " | ".join(["**" + m.name + "**" for m in self.raid.moves])
            )
            self.embed.set_thumbnail(url=self.raid.boss_url)

        else:
            formatted_start = self.raid.start.to("local").strftime(TIMEFORMAT_LONG)

            self.embed.description = (
                f"{tb.translate('Hatches')} <t:{self.raid.start.int_timestamp}:R>\n"
                f"{tb.translate('Raidzeit')}: **{formatted_start} – {formatted_end}**"
            )
            self.embed.set_thumbnail(url=self.raid.egg_url)

            if self.raid.boss:
                self.embed.title += " " + tb.translate("Egg")

        self.embed.description += "\n\n" + (
            f"[Google Maps]({GMAPS_LINK.format(self.gym.lat, self.gym.lon)}) | "
            f"[Apple Maps]({AMAPS_LINK.format(self.gym.lat, self.gym.lon)})"
        )

        self.embed.set_author(name=self.gym.name, icon_url=self.gym.img)

    def get_view(self) -> Optional[RaidInfoView]:
        if self.view and self.raid.boss:
            view = RaidInfoView(self)
        elif not self.view and self.post_to:
            view = RaidInfoView(self)
        else:
            view = None

        return view

    async def update_buttons(self) -> NoReturn:
        if not self.view:
            return

        new_view = self.get_view()

        if not new_view:
            await self.edit_message(new_view)
            return

        if len(new_view.children) != len(self.view.children):
            await self.edit_message(new_view)

    async def send_message(self) -> NoReturn:
        self.view = self.get_view()
        for channel in self.channels:
            message = await channel.send(embed=self.embed, view=self.view)
            self.messages.append(message)

    async def edit_message(self, view: Optional[RaidInfoView] = None) -> NoReturn:
        if not view:
            self.view = self.get_view()
        else:
            self.view = view
        for message in self.messages:
            await message.edit(embed=self.embed, view=self.view)

    async def delete(self) -> NoReturn:
        for message in self.messages:
            await message.delete()
