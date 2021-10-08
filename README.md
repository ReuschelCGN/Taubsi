# Taubsi

## Quick disclaimer

This is a raid bot i designed specifically to suit the needs of my community. Initially I put it on GitHub to streamline my personal workflow, however people were interested in the project and I decided to implement some things to make it work more universally.

Because of this, I don't like to take suggestions or help with any issues you have. Regardless, feel free to do the following:

- Open an issue on GitHub if you have a good suggestion
- DM me if you desperately need help
- If you think you encountered a bug, DM me about it first, then open an issue

## Features

There are 4 main features in this bot: Raid, RaidInfo, Setup, Dmap.

### Raids

- You're defining raid channels in which raids can be scheduled. Each raid channel is tied to a Raid level.
- In a raid channel, anyone can write. Talking should be disallowed, but I do allow very quick & short arranging (though this is happening very rarely)
- Raid channels should only be visble to players with a set team role. And no one should be able to add reactions in them
- fuzzywuzzy matching is used to match the written text to a gym name. If Taubsi is certain that your message is referencing a gym, a raid dialog starts
- The message must also contain a start time. It supports a few formats, but most commonly `13:00`, `13`, `13.00` are used. (these examples will all result in the same time)
- If your text matched multiple gyms, an additional message will be sent, asking you to select the gym you meant
- If everything is clear, Taubsi will send the raid dialog.
- The dialog will have "boss prediction". Meaning, that if the raid hasn't hatched yet and there's only one possible boss for that level, it will display that pokemon as the boss
- The dialog will also show additional info, depending on what is known. Below screenshot shows the maximum of information
- Below the dialog, there will be reactions showing numbers 1-6, a remote raid pass, a clock and a X
  - If you click on a number, you will join the raid with this amount of players
  - If you click the remote pass, A remote pass will display in front of your name indicating you're not physically there when the raid starts
  - The clock can be clicked if you're arriving max. 5 minutes too late (which should be used extremely rarely)
  - In the first 5 minutes, the creator of the raid dialog can delete it by pressing the X
- There will also be 2 buttons: One Google Maps link and a link to Pokebattler
- After the raid started, all reactions and buttons are removed
- Additionally, Each raid dialog comes with a role `gym name (13:00)`. This can be used in a separate channel to ping all raid members to i.e. ask them for an invite or to make other quick arrangements.

#### Raid notifications

While writing the readme, I'm noticing that I've actually forgotten to implement a way to toggle this. But /shrug

If you have a role called `RaidNotifications` or `RaidNachrichten` (whatever language you're using), you will receive private messages with updates on this raid. This includes messages for people joining or leaving. People clicking the clock or removing it. When the raid hatches. And when the raid is going to start in 5 minutes.

 
![image](https://user-images.githubusercontent.com/42342921/115625355-3df72f00-a2fc-11eb-9960-03338a747fa4.png)

### RaidInfo

- Additional raid info channels can be defined
- A raid info channel can have multiple levels and can be linked to multiple raid channels
- Each raid will have one message: If it hatched, the message is edited. If it despawns, the message is removed
- Each raid info will have a few buttons, these are suggestions for possible start times. If you click on a button, a raid dialog will be made in the linked raid channel. This basically skips the "writing in the channel part"

![image](https://media.discordapp.net/attachments/604038147109683200/877618125439389786/unknown.png)

### Setup

#### Team Choose channels

- A list of team choose channels can be defined
- A team choose channel should only have on message with 3 reactions for each team. The emojis should be called `mystic`, `instinct`, `valor`
- Set the permissions so nobody can add reactions

The goal is that new players can easily set their team by clicking on the team logo. This will give them a role, which is then used to determine the team in raid dialogs. You can also give the team roles their color.

There's also a team command that should be used more rarely. `!team [team]`. This is hardcoded to accept a few strings, mainly made for German

### Naming

- No one should be able to change their nickname
- Each player will have their level displayed in front of their name. E.g. `[49] Malte`
- Use `!level [lvl]` or `!l [lvl]` or `!lvl [lvl]` to set your level
- Use `!levelup` or `!lvlup` or `!up` to add +1 to your level
- Use `!name [name]` or `!n [name]` to set your name

# Setup

I'm not going into detail for setup. Basically you're going to make a new DB and use the sql commands in the sql/ folde on it. 

Then you're going to copy config.example.py to config.py and geofence.example.json to geofence.json and fill out both files. Custom emojis for the config can be found in the emojis/ directory

Now you're going to make a venv (important!) and install the requirements in it.

Now install discord.py 2.0 in it using `/path/to/venv/pip3 install git+https://github.com/jay3332/discord.py.git`

Now run start_taubsi.py and it should be fine.
