import json
from taubsi.utils.enums import Team
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from config.emotes import *

log = logging.getLogger("Raids")


class RaidMember:
    is_late: bool
    is_remote: bool
    is_invite: bool
    amount: int

    def __init__(self, raidmessage, user_id, amount):
        self.raidmessage = raidmessage

        self.member = raidmessage.message.guild.get_member(user_id)

        self.team = None
        roles = [role.name.lower() for role in self.member.roles]
        for team in Team:
            if team.name.lower() in roles:
                self.team = team
                break

        with open("config/config.json") as f:
            self.config = json.load(f)
        if self.config["notify_role"] in roles:
            self.is_subscriber = True
        else:
            self.is_subscriber = False

        self.update(amount)

    def update(self, amount=None):
        self.is_late = self.member.id in self.raidmessage.lates
        self.is_remote = self.member.id in self.raidmessage.remotes
        self.is_invite = self.member.id in self.raidmessage.invites

        if amount is not None:
            self.amount = amount

    async def make_role(self):
        if self.amount > 0:
            if self.raidmessage.role not in self.member.roles:
                await self.member.add_roles(self.raidmessage.role)
        else:
            if self.raidmessage.role in self.member.roles:
                await self.member.remove_roles(self.raidmessage.role)

    def make_text(self):
        text = self.member.display_name + f" ({self.amount})"
        if self.is_late:
            text = CONTROL_EMOJIS["late"] + " " + text
        if self.is_remote:
            text = CONTROL_EMOJIS["remote"] + " " + text
        if self.is_invite:
            text = text + " " + CONTROL_EMOJIS["invite"]
        return text + "\n"

    async def db_insert(self):
        keyvals = {
            "message_id": self.raidmessage.message.id,
            "user_id": self.member.id,
            "amount": self.amount,
            "is_late": self.is_late,
            "is_remote": self.is_remote,
            "is_invite": self.is_invite
        }
        await tb.intern_queries.insert("raidmembers", keyvals)
