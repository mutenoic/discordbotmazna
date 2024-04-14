import asyncio
import json
import logging
import os
import discord
from discord import app_commands
from discord.ext import commands
from config import bot, CommandInvokeError
import config
import random
import mutagen
from src import get_info


from commands.audio import *
from commands import games
from commands.movies import *
from commands.xp import *

logging.basicConfig(level=logging.WARN, filemode="w")
guilds = []
directory = os.getcwd()

if os.path.exists("./albumart.json"):
    with open("./albumart.json", "r") as cjson:
        albumart = json.load(cjson)
else:
    albumart = None


@bot.event
async def on_ready():
    print("Ready!")
    try:
        synced = await bot.tree.sync()
        print(f"synced {len(synced)} command")
    except Exception as e:
        print(e)

    global save_guild
    if not os.path.exists("./songs"):
        logging.warning(
            'Unable to find "songs" directory. Please ensure there is a "songs" directory present at the same level as this file'
        )
        return

    logging.info(f"{bot.user} has connected to Discord!")

    stage = None
    for guild in bot.guilds:
        for channel in guild.stage_channels:
            if channel.name == config.STAGENAME:
                stage = channel
                break
        if stage:
            break

    if not stage:
        logging.warning(
            f"Unable to find a text channel named {config.STAGENAME} in any guild.")
        return

    text_channel_list = []
    for guild in bot.guilds:
        for channel in guild.stage_channels:
            text_channel_list.append(channel)

    channel = stage.name
    global Vc
    global Tune
    try:
        Vc = await stage.connect()
        member = guild.me
        await member.edit(suppress=False)
    except CommandInvokeError:
        pass

    while True:
        while Vc.is_playing():
            await asyncio.sleep(1)
        else:
            Tune = get_info.write_song()
            Vc.play(discord.FFmpegPCMAudio(f"songs/{Tune}"))
            Vc.cleanup()
            audiofile = mutagen.File(f"songs/{Tune}")
            title = audiofile.get("title")[0]
            await bot.change_presence(activity=discord.Game(name=f"{title}"))
            Vc.source = discord.PCMVolumeTransformer(
                Vc.source, volume=config.VOLUME)
            if "suppress=False" in str(stage.voice_states):
                pass
            else:
                await member.edit(suppress=False)
            if queue and not Vc.is_playing():
                await play_next_song(stage)

if __name__ == "__main__":
    bot.run(config.TOKEN, reconnect=True)
