import sqlite3
import discord
from config import bot


def generateDb():
    conn = sqlite3.connect('xp.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS xp (user_id INTEGER, xp INTEGER)')
    conn.commit()
    conn.close()


@bot.event
async def on_message(message):
    generateDb()
    if not message.author.bot:
        conn = sqlite3.connect('xp.db')
        c = conn.cursor()

        c.execute('SELECT xp FROM xp WHERE user_id = ?', (message.author.id,))
        result = c.fetchone()

        if result is None:
            c.execute('INSERT INTO xp (user_id, xp) VALUES (?, ?)',
                      (message.author.id, 1))
        else:
            c.execute('UPDATE xp SET xp = xp + 1 WHERE user_id = ?',
                      (message.author.id,))

        conn.commit()
        current_xp = c.execute('SELECT xp FROM xp WHERE user_id = ?',
                               (message.author.id,)).fetchone()

        if current_xp[0] % 50 == 0 and current_xp[0] > 0:
            await message.channel.send(f'{message.author.mention} has reached {current_xp[0]} XP!')

        print(current_xp)
        conn.close()

    await bot.process_commands(message)
import discord
import sqlite3

@bot.tree.command(
    name='xp',
    description='Check your XP'
)
async def check_xp(interaction: discord.Interaction):
    generateDb()
    conn = sqlite3.connect('xp.db')
    c = conn.cursor()
    
    c.execute('SELECT xp FROM xp WHERE user_id = ?', (interaction.user.id,))
    result = c.fetchone()
    conn.close()
    
    if result is None:
        return await interaction.response.send_message('You have 0 XP')
    
    xp_amount = result[0]
    max_xp = 100
    xp_percentage = min(xp_amount / max_xp, 1.0)
    bar_length = 20
    filled_length = int(bar_length * xp_percentage)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    embed = discord.Embed(title="🌟 XP Information 🌟", description=f"You have {xp_amount} XP", color=discord.Color.gold())
    embed.add_field(name="Progress", value=f"`[{bar}]` {int(xp_percentage * 100)}%", inline=False)
    embed.set_author(name=f"🎮 {interaction.user.display_name} 🎮", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar_url)
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar_url)  # Profile picture as thumbnail
    embed.set_footer(text="🚀 Keep leveling up! 🚀")

    await interaction.response.send_message(embed=embed)
