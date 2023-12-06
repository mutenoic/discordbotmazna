# StageMusicBot - https://discord.gg/qBq2WSsgvv
import asyncio
import json
import logging
import os
import discord
import config
import mutagen
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError
from src import get_info
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.WARN, filemode="w")
guilds = []
directory = os.getcwd()

if os.path.exists("./albumart.json"):
    with open("./albumart.json", "r") as cjson:
        albumart = json.load(cjson)
else:
    albumart = None

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(config.PREFIX),
    intents=discord.Intents.all(),
)


@bot.event
async def on_ready():
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


@bot.event
async def on_voice_state_update(name, past, current):
    if current.channel == None and name.name == bot.user.id:
        logging.warning("Shutting down due to disconnect")
        logging.shutdown()
        await bot.close()
    else:
        # In this situation, the bot MAY still be disconnected, however I'm not sure on the fix for that unless I rewrite this first. It's a massive mess, but so far, an improvement
        pass


@bot.command(name="close")
async def close(ctx):
    logging.warning("Shutting down via command")
    logging.shutdown()
    await bot.close()


@bot.command(
    name="nowplaying",
    description="Command to check what song is currently playing",
    aliases=["np"],
)
async def nowplaying(ctx):
    try:
        if not Vc.is_playing():
            await ctx.reply("I need to play something first")
    except:
        await ctx.reply("I need to play something first")
    else:
        song_info = get_info.info(Tune)
        embed = discord.Embed(color=0xC0F207)
        embed.set_author(name="Now Playing 🎶", icon_url=ctx.guild.icon.url).add_field(
            name="Playing", value=f"{song_info[1]} - {song_info[0]}", inline=False
        ).set_footer(
            text="This bot is still in development, if you have any queries, please contact the owner",
            icon_url=(ctx.message.author.avatar.url),
        )
        if song_info[2] is not None:
            embed.add_field(name="Album", value=f"{song_info[2]}", inline=True)
            if albumart is not None:
                try:
                    embed.set_thumbnail(url=albumart[song_info[2]])
                except KeyError:
                    logging.warning("No Albumart found")
                    pass
        else:
            pass
        await ctx.reply(embed=embed)


@bot.command(name="play",
             description="Command to play a song",
             aliases=["p"],)
async def play(ctx, link):
    global Vc

    try:
        if ctx.author.voice is None:
            await ctx.reply("You need to be in a voice channel to use this command")
            return
        elif Vc is None:
            Vc = await ctx.author.voice.channel.connect()
        elif Vc.is_connected():
            pass
    except Exception as e:
        Vc = await ctx.author.voice.channel.connect()

    if Vc.is_playing():
        Vc.stop()

    try:
        # Check if the bot is already in a voice channel
        if not Vc:
            logging.warning("The bot is not in a voice channel.")
            return

        # Download the audio from the provided link
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        print(link)
        # Download the audio from the provided link
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            url = info_dict.get("url", None)

        # Update the song list
        # Tune = get_info.write_song()

        await ctx.reply(f"Now playing {info_dict['title']}")
        Vc.play(discord.FFmpegPCMAudio(
            url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

        # Update the presence with the new song title
        # audiofile = mutagen.File(url)
        # title = audiofile.get("title")[0]

    except Exception as e:
        logging.error(f"An error occurred while playing the song: {e}")

bot.run(config.TOKEN, reconnect=True)