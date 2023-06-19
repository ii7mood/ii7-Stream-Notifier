# Bot made by ii7moodUAE


# Import Packages
import discord
from discord import app_commands
import sqlite3
from os import getcwd, stat
from sys import path
from math import ceil

parent_path = getcwd().replace('/Discord BOT', '')
path.append(parent_path)

from common import log_wp, config

log_wp.name = __file__


db = sqlite3.connect('files/Streamers.db')
cursor = db.cursor()

# Set command prefix, and client
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
token = config['DISCORD']['token']


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='follow', description='Follow your favourite Twitch / YouTube streamer (Owner only)')
async def follow(interaction: discord.Interaction, name : str, url : str) -> None:
    
    if (not ("youtube" in url)) and (not ("twitch" in url)): # Minimal way of checking if URL is valid, not 100% but close enough I guess.
        await interaction.response.send_message("Please provide a valid URL!")
        return
    
    cursor.execute("SELECT * FROM streamers")
    streamer_list = cursor.fetchall()
    if (name in streamer_list) or (url in streamer_list): # Make sure no duplicate exists.
        await interaction.response.send_message(f"Duplicate detected, make sure this streamer has a unique name and is not already followed!")

    if url[-1] == "/":
        interaction.response.send_message("Make sure to leave the URL *without any forward-slashs at the end*")
        return
    
    if not("www" in url):
        interaction.response.send_message("Make sure that the url includes a 'www.' otherwise twitch pisses itself")
        return

    cursor.execute(f"INSERT INTO streamers (URL, RECORDED_ACTIVITY, NAME) VALUES (?, ?, ?)", (url, "not_live", name.lower()))
    db.commit()

    await interaction.response.send_message(f"Followed!")


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='unfollow', description='Unfollow any followed Twitch / YouTuber streamer! (Owner only)')
async def unfollow(interaction: discord.Interaction, name : str) -> None:
    cursor.execute(f"DELETE FROM streamers WHERE name = ?", (name.lower(),))
    db.commit()

    await interaction.response.send_message("Unfollowed!")


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='list', description='List all followed streamers! (Owner only)')
async def list(interaction: discord.Interaction) -> None:
    cursor.execute(f"SELECT * FROM streamers")
    raw_streamers_list = cursor.fetchall()

    streamers_list = []
    for streamer in raw_streamers_list:
        streamers_list.append(str(streamer[2]))

    message = " | ".join(streamers_list)
    await interaction.response.send_message(message)


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='search', description='Search the database with specific criteria')
async def search(interaction: discord.Interaction, criteria : str) -> None:

    states = ['is_upcoming', 'is_live', 'not_live']
    if criteria in states:
        cursor.execute("SELECT * FROM streamers WHERE RECORDED_ACTIVITY=?", (criteria,))
    
    else:
        cursor.execute("SELECT * FROM streamers WHERE NAME = ?", (criteria,))
    
    query = cursor.fetchall()

    if len(str(query)) > 2000:
        for i in range(0, ceil(len(query) / 20)):
            await interaction.channel.send(query[i * 20 : i * 20 + 20])
        return
        
    await interaction.response.send_message(query)


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='clean', description='Send empty unicode characters to "clean" chat!')
async def clean(interaction: discord.Interaction, number_of_characters : int) -> None:

    characters = []
    for x in range(number_of_characters):
        characters.append("ㅤ")
    
    await interaction.response.send_message("\n".join(characters))
    

@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='sync', description='Owner and Admins only')
async def sync(interaction: discord.Interaction):
    await tree.sync()
    await interaction.response.send_message(f"Synced!")


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name='reset', description='Reset certain properties of all streamers (Owner only)')
async def reset(interaction: discord.Interaction, property : str) -> None:
    cursor.execute(f"SELECT * FROM streamers")
    raw_streamers_list = cursor.fetchall() # raw_streamers_list has 3 elements, [url, activity, name]

    if property == "activity":
        for streamer in raw_streamers_list:
            cursor.execute(f"UPDATE streamers SET RECORDED_ACTIVITY = ? WHERE URL = ?", ('not_live', streamer[0]))
    
    elif property == "database":
        cursor.execute(f"DELETE FROM streamers;")
    
    else:
        await interaction.response.send_message("properties : 'activity' or 'database' (DELETES ALL RECORDS)")
        return
    
    db.commit()
    await interaction.response.send_message(f"Success!")


@app_commands.checks.has_permissions(administrator=True)
@tree.command(name="logs", description='Read the latest 2000 characters within the logs')
async def logs(interaction : discord.Interaction) -> None:

    fsize = stat('files/logs.log').st_size
    n = 1992 # not exactly 2000 as the '`' character is used six times and \n takes two spaces as well so 2000 - 8 has to be used.

    with open('files/logs.log') as f:
        if fsize < n:
            n = fsize
        
        else:
            f.seek(fsize - n) 
        fetched_lines = f.readlines()

        await interaction.response.send_message(f"```\n{''.join(fetched_lines)}```")



@client.event
async def on_ready():
    print("Ready!")

client.run(token)
