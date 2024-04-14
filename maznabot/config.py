import discord

from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError

TOKEN = "MTE4MjA0NzgzMDQ2Mjk2MzczMw.GsYUv2.HbsmU3U5RaBO7g7qnqQB4n84QM4XBlSdKXw5Cc"
PREFIX = "*"
BOTID = "1182047830462963733"
STAGENAME = "test"
MODROLE = "LEFYBOT"
VOLUME = 0.2
GUILDIDS = []


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX),
    intents=discord.Intents.all(),
)
