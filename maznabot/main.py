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

queue = []


async def play_next_song(ctx):
    global skip_song
    global Vc

    # If there are no songs in the queue, disconnect the bot from the voice channel and return
    if len(queue) == 0:
        await ctx.reply("Queue is empty, disconnecting")
        await Vc.disconnect()
        Vc = None
        return

    # If the skip_song variable was set to True, don't play the next song in the queue
    if skip_song:
        skip_song = False
        queue.pop(0)
        await play_next_song(ctx)
        return

    # Get the next song from the queue and play it
    url = queue.pop(0)
    await play_song(ctx, url)


async def play_song(ctx, url):
    global Vc, Tune

    try:
        if Vc is None or not Vc.is_connected():
            # Connect to the voice channel
            Vc = await ctx.author.voice.channel.connect()

        # Use youtube_dl to get the audio URL
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            audio_url = info_dict.get("url", None)

        print(f"Playing song: {url}")
        # Update the song list
        Tune = get_info.write_song()

        Vc.play(discord.FFmpegPCMAudio(
            audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

        # Update the queue list

        # Wait for the song to finish playing or for the user to skip it
        task = asyncio.create_task(while_playing_song(ctx))

        task.add_done_callback(lambda t: logging.info(
            f"Finished playing song: {url}"))
        # Update the presence with the new song title
        audiofile = mutagen.File(audio_url)
        title = audiofile.get("title")[0]
        await bot.change_presence(activity=discord.Game(name=f"{title}"))

    except Exception as e:
        logging.error(f"An error occurred while playing the song: {e}")


async def while_playing_song(ctx):
    global Vc, Tune, skip_song

    while Vc.is_playing():
        await asyncio.sleep(1)

    if (len(queue) > 0 and not Vc.is_playing()) and skip_song == False:
        await play_next_song(ctx)


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
            if queue and not Vc.is_playing():
                await play_next_song(stage)


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


@bot.command(name="pause", description="Command to pause the currently playing song")
async def pause(ctx):
    if Vc.is_playing():
        Vc.pause()
        await ctx.reply("Paused the song.")
    else:
        await ctx.reply("No song is currently playing.")


@bot.command(name="resume", description="Command to resume the paused song")
async def resume(ctx):
    if Vc.is_paused():
        Vc.resume()
        await ctx.reply("Resumed the song.")
    else:
        await ctx.reply("The song is not paused.")


@bot.command(name="skip", description="Command to skip the currently playing song")
async def skip(ctx):
    global skip_song

    if not Vc.is_playing():
        await ctx.reply("No song is currently playing.")
        return

    skip_song = True
    await ctx.reply("Skipped the song.")
    Vc.stop()

    await play_next_song(ctx)


@bot.command(
    name="play",
    description="Command to play a song",
    aliases=["p"],
)
async def play(ctx, link):
    global Vc, skip_song
    skip_song = False

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

        # Download the audio from the provided link
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            url = info_dict.get("url", None)

        # Enqueue the song

        # If the bot is not playing anything, start playing from the queue
        if not Vc.is_playing() and not Vc.is_paused():
            await play_next_song(ctx)

        queue.append(url)

        await ctx.reply(f"Queued {info_dict['title']}")

    except Exception as e:
        logging.error(f"An error occurred while queuing the song: {e}")

if __name__ == "__main__":
    bot.run(config.TOKEN, reconnect=True)
