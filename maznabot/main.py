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
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config.SPOTIPY_CLIENT_ID,
                                               client_secret=config.SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=config.SPOTIPY_REDIRECT_URI,
                                               scope=config.SPOTIPY_SCOPE))

queue = []

async def play_next_song(ctx):
    global skip_song
    global Vc

    if skip_song:
        skip_song = False
        if len(queue) > 0:
            await play_next_song(ctx)
        return

    if len(queue) == 0:
        return

    url = queue.pop(0)
    await play_song(ctx, url)

async def play_song(ctx, url):
    global Vc, Tune

    try:
        if Vc is None or not Vc.is_connected():
            Vc = await ctx.author.voice.channel.connect()

        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            audio_url = info_dict.get("url", None)

        print(f"Playing song: {url}")
        Tune = get_info.write_song()

        Vc.play(discord.FFmpegPCMAudio(
            audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

        task = asyncio.create_task(while_playing_song(ctx))

        task.add_done_callback(lambda t: logging.info(
            f"Finished playing song: {url}"))

        audiofile = mutagen.File(audio_url)
        title = audiofile.get("title")[0]
        await bot.change_presence(activity=discord.Game(name=f"{title}"))

    except Exception as e:
        logging.error(f"An error occurred while playing the song: {e}")
        
async def while_playing_song(ctx):
    global Vc, Tune, skip_song

    while Vc.is_playing() or Vc.is_paused():
        await asyncio.sleep(1)

    if len(queue) > 0 and not Vc.is_playing() and not skip_song:
        await play_next_song(ctx)


@bot.command(
    name="spotify",
    description="Command to search and play a song from Spotify",
)
async def spotify(ctx, *, query):
    global Vc, skip_song
    skip_song = False

    try:
        if ctx.author.voice is None:
            await ctx.reply("You need to be in a voice channel to use this command")
            return
        elif Vc is None or not Vc.is_connected():
            Vc = await ctx.author.voice.channel.connect()

    except Exception as e:
        Vc = await ctx.author.voice.channel.connect()

    try:
        results = sp.search(q=query, type='track', limit=1)

        if not results['tracks']['items']:
            await ctx.reply("No results found on Spotify.")
            return

        track_info = results['tracks']['items'][0]
        track_name = track_info['name']
        track_url = track_info['external_urls']['spotify']

        if not Vc.is_playing() and not Vc.is_paused():
            queue.append(track_url)
            await play_next_song(ctx)

        else:
            queue.append(track_url)
            await ctx.reply(f"Queued {track_name} from Spotify")

    except Exception as e:
        logging.error(f"An error occurred while queuing the song from Spotify: {e}")

@bot.command(
    name="spotify_playlist",
    description="Command to play a Spotify playlist",
)
async def spotify_playlist(ctx, playlist_url):
    global Vc, skip_song
    skip_song = False

    try:
        if ctx.author.voice is None:
            await ctx.reply("You need to be in a voice channel to use this command")
            return
        elif Vc is None or not Vc.is_connected():
            Vc = await ctx.author.voice.channel.connect()

    except Exception as e:
        Vc = await ctx.author.voice.channel.connect()

    try:
        playlist_id = playlist_url.split('/')[-1]
        results = sp.playlist_tracks(playlist_id)

        if not results['items']:
            await ctx.reply("No tracks found in the Spotify playlist.")
            return

        for track_info in results['items']:
            track_name = track_info['track']['name']
            track_url = track_info['track']['external_urls']['spotify']

            queue.append(track_url)

        if not Vc.is_playing() and not Vc.is_paused():
            await play_next_song(ctx)

        else:
            await ctx.reply(f"Queued {len(results['items'])} songs from Spotify playlist")

    except Exception as e:
        logging.error(f"An error occurred while queuing the Spotify playlist: {e}")

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

@bot.command(
    name="info",
    description="Command to show bot information and commands",
    aliases=["commands"]
)
async def bot_info(ctx):
    embed = discord.Embed(color=0x3498db, title="Bot Information", description="This bot is still in development.")
    embed.add_field(name="Commands", value="1. *play [link] - Play a song\n2. *pause - Pause the currently playing song\n3. *resume - Resume the paused song\n4. *skip - Skip the currently playing song\n5. *queue - Display the song queue\n6. *nowplaying - Check the currently playing song\n7. *info - Show bot information and commands\n8. *close - Shut down the bot", inline=False)
    await ctx.reply(embed=embed)

@bot.command(
    name="shuffle",
    description="Command to shuffle the song queue"
)
async def shuffle_queue(ctx):
    if len(queue) < 2:
        await ctx.reply("The queue must have at least two songs to be shuffled.")
        return

    import random
    random.shuffle(queue)
    await ctx.reply("The queue has been shuffled.")

@bot.event
async def on_voice_state_update(member, before, after):
    global Vc

    if member == bot.user and after.channel is None:
        logging.warning("Shutting down due to disconnect")
        logging.shutdown()
        await bot.close()

    if member == bot.user and before.channel is not None and after.channel is not None:
        if Vc and Vc.is_connected():
            await Vc.move_to(after.channel)
        else:
            Vc = await after.channel.connect()

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
@bot.command(
    name="skip",
    description="Command to skip the currently playing song"
)
async def skip(ctx):
    global skip_song

    if not Vc.is_playing():
        await ctx.reply("No song is currently playing.")
        return

    skip_song = True
    Vc.pause()  # Pause the current song instead of stopping it
    await ctx.reply("Skipped the song.")
    if len(queue) > 0:
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
        elif Vc is None or not Vc.is_connected():
            Vc = await ctx.author.voice.channel.connect()

    except Exception as e:
        Vc = await ctx.author.voice.channel.connect()

    try:
        if not Vc:
            logging.warning("The bot is not in a voice channel.")
            return

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            url = info_dict.get("url", None)

        if not Vc.is_playing() and not Vc.is_paused():
            queue.append(url)
            await play_next_song(ctx)
            await ctx.reply(f"Now playing {info_dict['title']}!")

        else:
            queue.append(url)
            await ctx.reply(f"Queued {info_dict['title']}")

    except Exception as e:
        logging.error(f"An error occurred while queuing the song: {e}")

@bot.command(
    name="queue",
    aliases=["q"]
)
async def show_queue(ctx):
    if not queue:
        await ctx.reply("The queue is empty.")
        return

    embed = discord.Embed(color=0x3498db, title="Song Queue", description="Here is the current song queue:")
    
    for i, url in enumerate(queue, start=1):
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get("title", "Unknown Title")
            duration = info_dict.get("duration", 0)
            minutes, seconds = divmod(duration, 60)
            duration_formatted = f"{minutes}:{seconds:02}"

        embed.add_field(name=f"#{i} - {title}", value=f"Duration: {duration_formatted}", inline=False)

    await ctx.reply(embed=embed)


if __name__ == "__main__":
    bot.run(config.TOKEN, reconnect=True)
