from yt_dlp import YoutubeDL
from src import get_info
from typing import Union
from config import bot
from main import albumart, discord, asyncio, logging, mutagen, random

current_song = {}
queue = []
async def play_next_song(ctx):
    global skip_song, current_song

    if skip_song:
        skip_song = False
        if len(queue) > 0:
            await play_next_song(ctx)
        return

    if len(queue) == 0:
        current_song = {}  # Reset current_song when the queue is empty
        return

    url = queue.pop(0)
    await play_song(ctx, url)

    # Update current_song with the information of the new song
    current_song = await get_info(url)
async def play_song(ctx, url, info_dict):
    global Vc, current_song

    try:
        if Vc is None or not Vc.is_connected():
            Vc = await ctx.author.voice.channel.connect()

        audio_url = info_dict.get("url", None)

        print(f"Playing song: {url}")
        current_song = info_dict  # Store the current song info

        Vc.play(discord.FFmpegPCMAudio(
            audio_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

        task = asyncio.create_task(while_playing_song(ctx))

        task.add_done_callback(lambda t: logging.info(
            f"Finished playing song: {url}"))

        title = current_song.get("title", "Unknown Title")
        await bot.change_presence(activity=discord.Game(name=f"{title}"))

    except Exception as e:
        logging.error(f"An error occurred while playing the song: {e}")


@bot.tree.command(
    name="play",
    description="Command to play a song"
)
async def play(interaction: discord.Interaction, link: str = None):
    global Vc, skip_song
    skip_song = False

    try:
        if interaction.user.voice is None:
            await interaction.response.send_message("You need to be in a voice channel to use this command", ephemeral=True)
            return
        elif Vc is None or not Vc.is_connected():
            Vc = await interaction.user.voice.channel.connect()

    except Exception as e:
        Vc = await interaction.user.voice.channel.connect()

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
            queue.append((url, info_dict))  # Pass URL along with song info
            await play_song(interaction, url, info_dict)  # Pass song info to play_song
            await interaction.response.send_message(f"Now playing {info_dict['title']}!", ephemeral=True)

        else:
            queue.append((url, info_dict))  # Pass URL along with song info
            await interaction.response.send_message(f"Queued {info_dict['title']}", ephemeral=True)

    except Exception as e:
        logging.error(f"An error occurred while queuing the song: {e}")

        
async def while_playing_song(ctx):
    global Vc, Tune, skip_song

    while Vc.is_playing() or Vc.is_paused():
        await asyncio.sleep(1)

    if len(queue) > 0 and not Vc.is_playing() and not skip_song:
        await play_next_song(ctx)

@bot.tree.command(name="pause", description="Command to pause the currently playing song")
async def pause(interaction: discord.Interaction):
    if Vc.is_playing():
        Vc.pause()
        await interaction.response.send_message("Paused the song.", ephemeral=True)
    else:
        await interaction.response.send_message("No song is currently playing.", ephemeral=True)

@bot.tree.command(name="resume", description="Command to resume the paused song")
async def resume(interaction: discord.Interaction):
    global Vc
    if Vc.is_paused():
        Vc.resume()
        await interaction.response.send_message("Resumed the song.", ephemeral=True)
    else:
        await interaction.response.send_message("The song is not paused.", ephemeral=True)

@bot.tree.command(
    name="skip",
    description="Command to skip the currently playing song"
)
async def skip(interaction: discord.Interaction):
    global skip_song

    if not Vc.is_playing():
        await interaction.response.send_message("No song is currently playing.", ephemeral=True)
        return

    skip_song = True
    Vc.pause()
    await interaction.response.send_message("Skipped the song.", ephemeral=True)
    if len(queue) > 0:
        await play_next_song(interaction)

@bot.tree.command(
    name="queue",
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

@bot.tree.command(
    name="info",
    description="Command to show bot information and commands",
)
async def bot_info(ctx):
    embed = discord.Embed(color=0x3498db, title="Bot Information", description="This bot is still in development.")
    embed.add_field(name="Commands", value="1. *play [link] - Play a song\n2. *pause - Pause the currently playing song\n3. *resume - Resume the paused song\n4. *skip - Skip the currently playing song\n5. *queue - Display the song queue\n6. *nowplaying - Check the currently playing song\n7. *info - Show bot information and commands\n8. *close - Shut down the bot", inline=False)
    await ctx.reply(embed=embed)

@bot.tree.command(
    name="shuffle",
    description="Command to shuffle the song queue"
)
async def shuffle_queue(ctx):
    if len(queue) < 2:
        await ctx.reply("The queue must have at least two songs to be shuffled.")
        return

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

@bot.tree.command(name="close")
async def close(ctx):
    logging.warning("Shutting down via command")
    logging.shutdown()
    await bot.close()


@bot.tree.command(
    name="nowplaying",
    description="Command to display the currently playing song"
)
async def now_playing(interaction: discord.Interaction):
    global current_song

    if current_song:
        title = current_song.get("title", "Unknown Title")
        artist = current_song.get("artist", "Unknown Artist")
        album = current_song.get("album", "Unknown Album")
        duration = current_song.get("duration", 0)

        embed = discord.Embed(
            color=0x3498db,
            title="Now Playing",
            description=f"**[{title} - {artist}]** from **{album}**"
        )

        embed.add_field(name="Duration", value=str(duration // 60) + ':' + str(duration % 60).zfill(2), inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("No song is currently playing.")
