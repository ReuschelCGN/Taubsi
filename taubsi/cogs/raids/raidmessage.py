import json
from math import floor, ceil

import discord
import arrow

from taubsi.utils.utils import asyncget, reverse_get
from taubsi.utils.enums import Team
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from config.emotes import *
from taubsi.cogs.raids.raidmember import RaidMember
from taubsi.cogs.raids.pogo import Gym, BaseRaid, ScannedRaid

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

    @discord.ui.button(label="Mit Fern-Pass", style=discord.ButtonStyle.blurple, emoji="✈")
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

    @discord.ui.button(label="Mit Einladung", style=discord.ButtonStyle.blurple, emoji="📩")
    async def invite(self, button: discord.ui.Button, interaction: discord.Interaction):
        member = self.raidmessage.get_member(interaction.user.id)
        if not member:
            member = RaidMember(self.raidmessage, interaction.user.id, 1)
            self.raidmessage.members.append(member)

        if interaction.user.id in self.raidmessage.invites:
            self.raidmessage.invites.remove(interaction.user.id)
        else:
            self.raidmessage.invites.append(interaction.user.id)

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
    def __init__(self):
        self.embed = discord.Embed()
        self.channel_settings = None

        self.channel_id = 0
        self.message_id = 0
        self.message = None
        self.init_message_id = 0
        self.init_message = None
        self.author_id = 0

        self.start_time = arrow.get(2020, 1, 1, 12, 0)
        self.role = None
        self.view = None

        self.gym = Gym()
        self.raid = None

        self.footer_prefix = ""
        self.warnings = set()
        self.static_warnings = set()

        self.members = []
        self.remotes = []
        self.invites = []
        self.lates = []

        self.notified_5_minutes = False

    @property
    def total_amount(self):
        return sum([m.amount for m in self.members])

    @property
    def formatted_start(self):
        return self.start_time.strftime(timeformat)

    async def from_raidinfo(self, gym, raid, start_time, interaction, channel_id):
        self.gym = gym
        self.start_time = start_time
        self.channel_id = channel_id
        self.channel_settings = tb.raid_channels[self.channel_id]

        self.author_id = interaction.user.id
        self.footer_prefix = tb.translate("Scheduled_by").format(interaction.user.display_name) + "\n"
        self.raid = raid
        await self.send_message()

    async def from_command(self, gym, start_time, init_message):
        self.gym = gym

        self.start_time = start_time
        self.channel_id = init_message.channel.id
        self.channel_settings = tb.raid_channels[self.channel_id]

        self.init_message = init_message
        self.init_message_id = init_message.id
        self.author_id = self.init_message.author.id

        self.raid = await self.gym.get_active_raid(self.channel_settings["level"])
        await self.send_message()

    async def from_db(self, channel_id, message_id, init_message_id, start_time, gym_id, role_id):
        self.text = ""
        self.channel_id = channel_id
        self.message_id = message_id
        self.start_time = arrow.get(start_time).to("local")
        self.init_message_id = init_message_id
        self.channel_settings = tb.raid_channels[self.channel_id]

        channel = await tb.bot.fetch_channel(self.channel_id)
        self.message = await channel.fetch_message(self.message_id)
        self.gym = [g for g in tb.gyms[self.message.guild.id] if g.id == gym_id][0]
        self.role = self.message.guild.get_role(role_id)
        self.raid = await self.gym.get_active_raid(self.channel_settings["level"])

        try:
            self.init_message = await channel.fetch_message(self.init_message_id)
        except:
            self.init_message = self.message
        self.author_id = self.init_message.author.id

        raidmember_db = await tb.intern_queries.execute(
            f"select user_id, amount, is_late, is_remote, is_invite from raidmembers where message_id = {self.message.id}")
        for entry in raidmember_db:
            if entry[2]:
                self.lates.append(entry[0])
            if entry[3]:
                self.remotes.append(entry[0])
            if entry[4]:
                self.invites.append(entry[0])
            raidmember = RaidMember(self, entry[0], entry[1])
            self.members.append(raidmember)

        self.embed = self.message.embeds[0]
        await self.make_member_fields()
        await self.make_base_embed()
        self.make_warnings()
        await self.edit_message()

    async def get_message(self):
        channel = await tb.bot.fetch_channel(self.channel_id)
        message = await channel.fetch_message(self.message_id)
        return message

    def get_member(self, user_id: int):
        for member in self.members:
            if member.member.id == user_id:
                return member
        return None

    async def add_reaction(self, payload):
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
            elif control == "invite":
                self.invites.append(payload.user_id)

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

    async def remove_reaction(self, payload):
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
            elif control == "invite":
                self.invites.remove(payload.user_id)

        elif emote in NUMBER_EMOJIS.values():
            if member.amount > 0:
                await self.notify(f"❌ {member.member.display_name} ({member.amount})", member.member)
                amount = 0

        member.update(amount)
        await self.make_member_fields()
        await member.make_role()
        await member.db_insert()

    async def notify(self, message: str, user=None):
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

    def make_warnings(self):
        self.embed.description = self.text
        for warning in self.static_warnings.union(self.warnings):
            self.embed.description += "\n" + warning

    async def make_base_embed(self):
        self.embed.title = self.raid.name + ": " + self.gym.name
        # self.embed.url = "https://google.com/"
        # difficulty = await self.get_difficulty()

        # Description based on what info is available
        self.text = tb.translate("Start") + f": **{self.formatted_start}** " \
                    + f"<t:{self.start_time.int_timestamp}:R>" + "\n\n"
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

    async def set_image(self):
        url = await self.raid.get_image()
        self.embed.set_thumbnail(url=url)
        await self.edit_message()

    def make_footer(self, amount: int = 0):
        self.embed.set_footer(text=self.footer_prefix + tb.translate("Total") + f": {amount}")

    async def make_member_fields(self):
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

        total_remote = (sum(m.amount for m in self.members if m.is_remote) + sum(m.amount for m in self.members if m.is_invite))
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

    async def db_insert(self):
        keyvals = {
            "channel_id": self.message.channel.id,
            "message_id": self.message.id,
            "init_message_id": self.init_message_id,
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

    async def edit_message(self):
        log.info(f"Editing message {self.message.id}")
        await self.message.edit(embed=self.embed, view=RaidmessageView(self))

    async def send_message(self):
        channel = await tb.bot.fetch_channel(self.channel_id)
        await self.make_base_embed()
        self.make_footer()

        self.message = await channel.send(embed=self.embed, view=RaidmessageView(self))
        self.message_id = self.message.id

        self.role = await channel.guild.create_role(name=f"{self.gym.name} ({self.formatted_start})", mentionable=True)

    async def delete_role(self):
        await self.role.delete()

    async def end_raid(self):
        log.info(f"Raid {self.message.id} started. Clearing reactions and deleting its role.")

        await self.message.edit(embed=self.embed, view=None)
        await self.message.clear_reactions()
        await self.delete_role()
