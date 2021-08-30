# Taubsi 2.0

This is a raid bot designed specifically to suit the needs of my community.

## Features

There are 3 main cogs in this bot: Raid, RaidInfo, Setup.

### Raids

- You're defining raid channels in which raids can be scheduled. Each raid channel is tied to a Raid level.
- In a raid channel, anyone can write. Talking should be disallowed, but I do allow very quick & short arranging (though this is happening very rarely)
- Raid channels should be locked to only players with set team roles. And no one should be able to add reactions in them
- fuzzywuzzy matching is used to match the written text to a gym name. If Taubsi is certain that your message is referencing a gym, a raid dialog starts
- The message must also contain a start time. It supports a few formats, but most commonly `13:00`, `13`, `13.00` are used. (these examples will all result in the same time)
- If your text matched multiple gyms, an additional message will be sent, asking you to select the gym you meant
- If everything is clear, Taubsi will send the raid dialog.
- The dialog will have "boss prediction". Meaning, that if the raid hasn't hatched yet and there's only one possible boss for that level, it will display that pokemon as the boss
- The dialog will also show additional info, depending on what is known. Below screenshot shows the maximum of information
- Below the dialog, there will be reactions showing numbers 1-6, a remote raid pass, a clock, a invite and a X
  - If you click on a number, you will join the raid with this amount of players
  - If you click the remote pass, a remote pass will display in front of your name indicating you're not physically there when the raid starts
  - If you click the invite, a invite will be display behind of your name indicating you need an invitation for the raid and with `!inv` you could post your friendcode and trainername under the raidmessage. So the other raidmembers could copy&past the code direct in pokemon go.
  - The clock can be clicked if you're arriving max. 5 minutes too late (which should be used extremely rarely)
  - In the first 5 minutes, the creator of the raid dialog can delete it by pressing the X
- There will also be 2 buttons: One Google Maps link and a link to Pokebattler
- After the raid started, all reactions and buttons are removed
- Additionally, Each raid dialog comes with a role `gym name (13:00)`. This can be used in a separate channel to ping all raid members to i.e. ask them for an invite or to make other quick arrangements.

#### Raid notifications

If you define a role in `config.json` -> `"notify_role": "desired Rolename"` (whatever you're using), that you have also in discord, you will receive private messages with updates on this raid. This includes messages for people joining or leaving. People clicking the clock or removing it. When the raid hatches. And when the raid is going to start in 5 minutes.

 
![image](https://user-images.githubusercontent.com/42342921/115625355-3df72f00-a2fc-11eb-9960-03338a747fa4.png)

### RaidInfo

- Additional raid info channels can be defined
- A raid info channel can have multiple levels and can be linked to multiple raid channels
- Each raid will have one message: If it hatched, the message is edited. If it despawns, the message is removed
- Each raid info will have a few buttons, these are suggestions for possible start times. If you click on a button, a raid dialog will be made in the linked raid channel. This basically skips the "writing in the channel part"

![image](https://media.discordapp.net/attachments/604038147109683200/877618125439389786/unknown.png)

### Commands to interact with the BOT

in Setup Channel:

 `!name NAME` -> your PoGo Trainer Name
 
 `!lvl LEVEL` -> add your Trainer Level to Nickname
 
 `!lvlup` -> Trainer Level +1
 
 `!code CODE` -> add your Friendcode (!code 123412341234)
 
 `!code anzeigen` - > shows your stored friendcode
 
 `!team COLOR` -> add your Teamcolor
 
in Raid Channel:

 `GYM-Name HH:MM`
 
 `!inv` -> for Invitation  (Hint: `!inv @MAXMUSTERMAN` for Invitation from User MAXMUSTERMAN)

# INSTALLATION

1. Clone repository `git clone https://github.com/ReuschelCGN/Taubsi`
2. Copy content of `docker-compose.yml` into your running `docker-compose.yml`
3. Create a new bot in Discord, assign rights and invite to your server!
4. Create a new database with name `taubsi` collation `utf8mb4_unicode_ci` and import `./sql/taubsi.sql` into it.
5. Rename folder `config_example` to `config` and fill out the files:
   - `config.json`
   - `geofence.json`
   - `servers.json`
6. Insert your own Team emojis into -> `./config/emotes.py` if desired
7. `sudo docker-compose build taubsi`
8. `sudo docker-compose up -d taubsi`

get logs: `sudo docker-compose logs -f taubsi`

# Additional IMPORTANT Infos:
This is a Fork from Maltes Taubsi Raidbot -> https://github.com/ccev/Taubsi

Many thanks to him for his original!
