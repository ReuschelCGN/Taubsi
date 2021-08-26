from __future__ import annotations
import json
from math import floor, ceil
from typing import List, Set, Optional, TYPE_CHECKING, NoReturn, Union

import discord
import arrow

from taubsi.utils.utils import asyncget, reverse_get
from taubsi.utils.enums import Team
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from config.emotes import *
from taubsi.cogs.raids.raidmember import RaidMember
from taubsi.cogs.raids.pogo import Gym, BaseRaid, ScannedRaid

if TYPE_CHECKING:
    from datetime import datetime

log = logging.getLogger("Raids")

timeformat = tb.translate("timeformat_short")

TOTAL_LIMIT = 20
REMOTE_LIMIT = 10

GMAPS_LINK = "https://www.google.com/maps/search/?api=1&query={},{}"
AMAPS_LINK = "https://maps.apple.com/maps?daddr={},{}"
PBATTLER_LINK = (
    "https://www.pokebattler.com/raids/defenders/{}/levels/RAID_LEVEL_{}/attackers/levels/40/strategies/"
    "CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC?sort=ESTIMATOR&weatherCondition=NO_WEATHER"
    "&dodgeStrategy=DODGE_REACTION_TIME&aggregation=AVERAGE&includeLegendary=true&includeShadow=true"
    "&includeMegas=true&attackerTypes=POKEMON_TYPE_ALL"
)


"""
class RaidmessageView(discord.ui.View):
    def __init__(self, raidmessage):
        super().__init__()
        self.raidmessage = raidmessage

    @discord.ui.button(label="Anmelden (+1)", style=discord.ButtonStyle.green)
    async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = self.raidmessage.get_member(interaction.user.id)
        if not member:
            member = RaidMember(self.raidmessage, interaction.user.id, 0)
            self.raidmessage.members.append(member)

        amount = member.amount + 1
        notification = f"▶️ {member.member.display_name} ({amount})"

        member.update(amount)
        await self.raidmessage.make_member_fields()
        await self.raidmessage.notify(notification, member.member)
        await member.make_role()
        await member.db_insert()

    @discord.ui.button(label="Abmelden (-1)", style=discord.ButtonStyle.grey)
    async def leave(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = self.raidmessage.get_member(interaction.user.id)

        amount = member.amount - 1
        notification = f"▶️ {member.member.display_name} ({amount})"

        member.update(amount)
        await self.raidmessage.make_member_fields()
        await self.raidmessage.notify(notification, member.member)
        await member.make_role()
        await member.db_insert()

    @discord.ui.button(label="Komme Später", style=discord.ButtonStyle.grey, emoji="🕐")
    async def late(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = self.raidmessage.get_member(interaction.user.id)
        if not member:
            member = RaidMember(self.raidmessage, interaction.user.id, 1)
            self.raidmessage.members.append(member)

        notification = False

        if interaction.user.id in self.raidmessage.lates:
            self.raidmessage.lates.remove(interaction.user.id)
            if member.amount > 0:
                notification = f"{member.member.display_name} kommt doch pünktlich", member.member
        else:
            self.raidmessage.lates.append(interaction.user.id)
            notification = f"🕐 {member.member.display_name}"

        member.update()
        await self.raidmessage.make_member_fields()
        if notification:
            await self.raidmessage.notify(notification, member.member)
        await member.make_role()
        await member.db_insert()

    @discord.ui.button(label="Mit Fern-Pass", style=discord.ButtonStyle.blurple, emoji="<:fernraid:728917159216021525>")
    async def remote(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = self.raidmessage.get_member(interaction.user.id)
        if not member:
            member = RaidMember(self.raidmessage, interaction.user.id, 1)
            self.raidmessage.members.append(member)

        if interaction.user.id in self.raidmessage.remotes:
            self.raidmessage.remotes.remove(interaction.user.id)
        else:
            self.raidmessage.remotes.append(interaction.user.id)

        member.update()
        await self.raidmessage.make_member_fields()
        await member.make_role()
        await member.db_insert()

    @discord.ui.button(label="Löschen", style=discord.ButtonStyle.red, emoji="❌")
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.raidmessage.init_message.author.id:
            await interaction.message.delete()
            
"""


class RaidmessageView(discord.ui.View):
    def __init__(self, raidmessage):
        super().__init__()

        maps_link = GMAPS_LINK.format(
            raidmessage.gym.lat, raidmessage.gym.lon
        )
        self.add_item(discord.ui.Button(url=maps_link, label="Google Maps", style=discord.ButtonStyle.link))

        if raidmessage.raid.boss:
            if raidmessage.raid.level == 6:
                pb_level = "MEGA"
            else:
                pb_level = str(raidmessage.raid.level)
            pb_link = PBATTLER_LINK.format(raidmessage.raid.pokebattler_name, pb_level)
            self.add_item(discord.ui.Button(url=pb_link, label="Pokebattler", style=discord.ButtonStyle.link))


class RaidMessage:
    text: str
    embed: discord.Embed
    start_time: arrow.Arrow
    raid: Union[BaseRaid, ScannedRaid]

    channel_id: int
    message: discord.Message
    init_message: Optional[discord.Message]
    author_id: Optional[int]

    role: discord.Role
    view: RaidmessageView
    footer_prefix: str
    warnings: Set[str]
    static_warnings: Set[str]

    members: List[RaidMember]
    remotes: List[int]
    lates: List[int]

    notified_5_minutes: bool = False

    def __init__(self, gym: Gym, start: arrow.Arrow, channel_id: int):
        self.embed = discord.Embed()

        self.gym = gym
        self.start_time = start
        self.channel_id = channel_id

        self.channel_settings = tb.raid_channels[self.channel_id]

        self.text = ""
        self.footer_prefix = ""
        self.members = []
        self.remotes = []
        self.lates = []
        self.warnings = set()
        self.static_warnings = set()

    @classmethod
    async def from_raidinfo(cls,
                            gym: Gym, raid: BaseRaid, start_time: arrow.Arrow,
                            interaction: discord.Interaction, channel_id: int) -> RaidMessage:
        self = cls(gym, start_time, channel_id)

        self.author_id = interaction.user.id
        self.footer_prefix = tb.translate("Scheduled_by").format(interaction.user.display_name) + "\n"
        self.raid = raid
        self.init_message = None
        self.view = self._get_view()

        await self.send_message()
        return self

    @classmethod
    async def from_command(cls, gym: Gym, start_time: arrow.Arrow, init_message: discord.Message) -> RaidMessage:
        self = cls(gym, start_time, init_message.channel.id)

        self.raid = await self.gym.get_active_raid(self.channel_settings["level"])
        self.init_message = init_message
        self.author_id = self.init_message.author.id
        self.view = self._get_view()

        await self.send_message()
        return self

    @classmethod
    async def from_db(cls, channel_id: int, message_id: int, init_message_id: int, start_time: datetime,
                      gym_id: int, role_id: int) -> RaidMessage:
        start = arrow.get(start_time).to("local")
        channel: discord.TextChannel = await tb.bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        gym = [g for g in tb.gyms[message.guild.id] if g.id == gym_id][0]

        self = cls(gym, start, channel_id)

        self.message = message
        self.role = self.message.guild.get_role(role_id)
        self.raid = await self.gym.get_active_raid(self.channel_settings["level"])

        try:
            self.init_message = await channel.fetch_message(init_message_id)
            self.author_id = self.init_message.author.id
        except discord.NotFound:
            self.init_message = None
            self.author_id = None

        raidmember_db = await tb.intern_queries.execute(
            f"select user_id, amount, is_late, is_remote from raidmembers where message_id = {self.message.id}")
        for entry in raidmember_db:
            if entry[2]:
                self.lates.append(entry[0])
            if entry[3]:
                self.remotes.append(entry[0])
            raidmember = RaidMember(self, entry[0], entry[1])
            self.members.append(raidmember)

        self.embed = self.message.embeds[0]
        await self.make_member_fields()
        await self.make_base_embed()
        self.make_warnings()
        self.view = self._get_view()
        await self.edit_message()

        return self

    def _get_view(self) -> RaidmessageView:
        return RaidmessageView(self)

    @property
    def total_amount(self) -> int:
        return sum([m.amount for m in self.members])

    @property
    def formatted_start(self) -> str:
        return self.start_time.strftime(timeformat)

    def get_member(self, user_id: int) -> Optional[RaidMember]:
        for member in self.members:
            if member.member.id == user_id:
                return member
        return None

    async def add_reaction(self, payload: discord.RawReactionActionEvent) -> NoReturn:
        emote = str(payload.emoji)
        member = self.get_member(payload.user_id)
        amount = None
        to_notify = False
        notification = ""
        if not member:
            member = RaidMember(self, payload.user_id, 1)
            self.members.append(member)

        if emote in CONTROL_EMOJIS.values():
            control = reverse_get(CONTROL_EMOJIS, emote)

            if control == "remove":
                if payload.user_id == self.author_id:
                    await self.message.delete()
                    return
            elif control == "late":
                self.lates.append(payload.user_id)
                notification = f"🕐 {member.member.display_name}"
                to_notify = True
            elif control == "remote":
                self.remotes.append(payload.user_id)

        elif emote in NUMBER_EMOJIS.values():
            amount = reverse_get(NUMBER_EMOJIS, emote)
            notification = f"▶️ {member.member.display_name} ({amount})"
            to_notify = True

        else:
            return

        member.update(amount)
        await self.make_member_fields()
        if to_notify:
            await self.notify(notification, member.member)
        await member.make_role()
        await member.db_insert()

    async def remove_reaction(self, payload: discord.RawReactionActionEvent) -> NoReturn:
        member = self.get_member(payload.user_id)
        if not member:
            return

        # code duplication :thumbsdown:
        amount = None
        emote = str(payload.emoji)
        if emote in CONTROL_EMOJIS.values():
            control = reverse_get(CONTROL_EMOJIS, emote)

            if control == "late":
                self.lates.remove(payload.user_id)
                if member.amount > 0:
                    await self.notify(tb.translate("notify_on_time").format(member.member.display_name), member.member)
            elif control == "remote":
                self.remotes.remove(payload.user_id)

        elif emote in NUMBER_EMOJIS.values():
            if member.amount > 0:
                await self.notify(f"❌ {member.member.display_name} ({member.amount})", member.member)
                amount = 0

        member.update(amount)
        await self.make_member_fields()
        await member.make_role()
        await member.db_insert()

    async def notify(self, message: str, user: Optional[discord.User] = None) -> NoReturn:
        log.info(f"Raid notification: {message}")
        for member in self.members:
            if not member.is_subscriber:
                continue
            if member.amount == 0:
                continue
            if user is not None and user.id == member.member.id:
                continue

            embed = discord.Embed()
            embed.title = self.gym.name
            embed.url = self.message.jump_url
            embed.description = message

            await member.member.send(embed=embed)

    async def get_difficulty(self):
        # unused
        if not self.raid.boss:
            return None
        try:
            pb_mon_name = self.raid.boss.base_template
            if self.raid.boss.temp_evolution_id > 0:
                pb_mon_name += "_" + self.raid.boss.temp_evolution_template
            path = f"config/pokebattler/{pb_mon_name}.json"
            try:
                with open(path, "r") as f:
                    pb_data = json.load(f)
            except FileNotFoundError:
                if self.raid.level == 6:
                    level = "MEGA"
                else:
                    level = self.raid.level
                url = f"https://fight.pokebattler.com/raids/defenders/{pb_mon_name}/levels/RAID_LEVEL_{level}/" \
                      f"attackers/levels/35/strategies/CINEMATIC_ATTACK_WHEN_POSSIBLE/DEFENSE_RANDOM_MC" \
                      f"?sort=ESTIMATOR&weatherCondition=NO_WEATHER&dodgeStrategy=DODGE_REACTION_TIME" \
                      f"&aggregation=AVERAGE&randomAssistants=-1&includeLegendary=true&includeShadow=false" \
                      f"&attackerTypes=POKEMON_TYPE_ALL"
                pb_data_raw = await asyncget(url)
                pb_data_raw = json.loads(pb_data_raw.decode("utf-8"))
                pb_data = {}

                attackers = pb_data_raw["attackers"][0]
                for data in attackers["byMove"]:
                    move1 = data["move1"]
                    move2 = data["move2"]
                    pb_data[move1 + "+" + move2] = data["total"]
                pb_data["?"] = attackers["randomMove"]["total"]

                with open(path, "w+") as f:
                    f.write(json.dumps(pb_data))

            if isinstance(self.raid, BaseRaid) or not self.raid.moves[0]:
                estimator = pb_data["?"]
            else:
                estimator = pb_data["+".join([m.template for m in self.raid.moves])]

            estimator = estimator["estimator"]

            if self.total_amount < estimator:
                if self.total_amount < estimator - 0.3:
                    difficulty = 0
                else:
                    difficulty = 1
            else:
                if self.total_amount <= ceil(estimator):
                    difficulty = 2
                elif self.total_amount <= ceil(estimator) + 1:
                    difficulty = 3
                else:
                    difficulty = 4

            if self.total_amount < floor(estimator):
                difficulty = 0

            if self.total_amount == 0:
                difficulty = 0

            self.embed.color = DIFFICULTY_COLORS[difficulty]

            return DIFFICULTY_NAMES[difficulty] + "\n\n"


        except Exception as e:
            log.exception(e)
            return None

    def make_warnings(self) -> NoReturn:
        self.embed.description = self.text
        for warning in self.static_warnings.union(self.warnings):
            self.embed.description += "\n" + warning

    async def make_base_embed(self) -> NoReturn:
        self.embed.title = self.raid.name + ": " + self.gym.name
        # self.embed.url = "https://google.com/"
        # difficulty = await self.get_difficulty()

        # Description based on what info is available
        self.text = f"{tb.translate('Start')}: **{self.formatted_start}** <t:{self.start_time.int_timestamp}:R>\n\n"
        if self.raid.boss:
            self.text += f"100%: **{self.raid.cp20}** | **{self.raid.cp25}**\n"
        if isinstance(self.raid, ScannedRaid):
            if self.raid.moves[0]:
                self.text += tb.translate("Moves") + ": " \
                             + " | ".join(["**" + m.name + "**" for m in self.raid.moves]) + "\n"

            format_start = self.raid.start.to('local').strftime(timeformat)
            format_end = self.raid.end.to('local').strftime(timeformat)
            self.text += tb.translate("Raidzeit") + f": **{format_start}** – **{format_end}**\n"
        self.make_warnings()

    async def set_image(self) -> NoReturn:
        url = await self.raid.get_image()
        self.embed.set_thumbnail(url=url)
        await self.edit_message()

    def make_footer(self, amount: int = 0) -> NoReturn:
        self.embed.set_footer(text=f"{self.footer_prefix}{tb.translate('Total')}: {amount}")

    async def make_member_fields(self) -> NoReturn:
        self.embed.clear_fields()
        for team in Team:
            if team.value == 0:
                continue
            emoji = TEAM_EMOJIS[team.value]

            index = 0
            for field in self.embed.fields:
                if emoji in field.name:
                    break
                index += 1

            members = [m for m in self.members if m.team == team]
            team_amount = sum([m.amount for m in members])

            if team_amount > 0:
                field_name = f"{emoji} ({team_amount})"
                field_value = ""
                for member in members:
                    if member.amount > 0:
                        field_value += member.make_text()
                self.embed.insert_field_at(index=index, name=field_name, value=field_value, inline=False)

        self.make_footer(self.total_amount)

        self.warnings.clear()

        total_remote = sum(m.amount for m in self.members if m.is_remote)
        remote_cap = (total_remote > REMOTE_LIMIT - 2)
        total_cap = (self.total_amount > TOTAL_LIMIT - 2)
        if remote_cap and total_cap:
            self.warnings.add(tb.translate("warn_too_many_both").format(TOTAL_LIMIT, REMOTE_LIMIT))
        elif remote_cap:
            self.warnings.add(tb.translate("warn_too_many_remote").format(REMOTE_LIMIT))
        elif total_cap:
            self.warnings.add(tb.translate("warn_too_many_total").format(TOTAL_LIMIT))

        if [m for m in self.members if m.is_late]:
            self.warnings.add(tb.translate("warn_is_late"))

        self.make_warnings()
        await self.edit_message()

    async def db_insert(self) -> NoReturn:
        keyvals = {
            "channel_id": self.message.channel.id,
            "message_id": self.message.id,
            "init_message_id": self.init_message.id if self.init_message else 0,
            "gym_id": self.gym.id,
            "start_time": self.start_time.to("utc").naive,
            "raid_level": self.raid.level,
            "role_id": self.role.id
        }
        if self.raid.boss:
            keyvals["mon_id"] = self.raid.boss.id
            keyvals["mon_form"] = self.raid.boss.form
        if isinstance(self.raid, ScannedRaid):
            keyvals["raid_start"] = self.raid.start.naive
            keyvals["raid_end"] = self.raid.end.naive

        await tb.intern_queries.insert("raids", keyvals)

    async def edit_message(self) -> NoReturn:
        log.info(f"Editing message {self.message.id}")
        await self.message.edit(embed=self.embed, view=self.view)

    async def send_message(self) -> NoReturn:
        channel = await tb.bot.fetch_channel(self.channel_id)
        await self.make_base_embed()
        self.make_footer()

        self.message = await channel.send(embed=self.embed, view=self.view)
        self.role = await channel.guild.create_role(name=f"{self.gym.name} ({self.formatted_start})", mentionable=True)

    async def end_raid(self) -> NoReturn:
        log.info(f"Raid {self.message.id} started. Clearing reactions and deleting its role.")

        await self.message.edit(embed=self.embed, view=None)
        await self.message.clear_reactions()
        await self.role.delete()
