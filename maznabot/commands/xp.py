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
    # Check if the message is not from a bot
    generateDb()
    if not message.author.bot:
        # Connect to the database
        conn = sqlite3.connect('xp.db')
        c = conn.cursor()

        # Check if the user already exists in the database
        c.execute('SELECT xp FROM xp WHERE user_id = ?', (message.author.id,))
        result = c.fetchone()

        if result is None:
            # If the user doesn't exist, insert a new row with initial XP
            c.execute('INSERT INTO xp (user_id, xp) VALUES (?, ?)',
                      (message.author.id, 1))
        else:
            # If the user exists, update their XP by incrementing it
            c.execute('UPDATE xp SET xp = xp + 1 WHERE user_id = ?',
                      (message.author.id,))

        # Commit the changes and close the connection
        conn.commit()
        current_xp = c.execute('SELECT xp FROM xp WHERE user_id = ?',
                               (message.author.id,)).fetchone()

        if current_xp[0] % 50 == 0 and current_xp[0] > 0:
            await message.channel.send(f'{message.author.mention} has reached {current_xp[0]} XP!')

        print(current_xp)
        conn.close()

    # Let the message continue processing
    await bot.process_commands(message)


@bot.command(
    name='xp',
    description='Check your XP',
)
async def check_xp(ctx):
    generateDb()
    conn = sqlite3.connect('xp.db')
    c = conn.cursor()
    c.execute('SELECT xp FROM xp WHERE user_id = ?', (ctx.author.id,))
    result = c.fetchone()
    conn.close()
    if result is None:
        return await ctx.send('You have 0 XP')
    return await ctx.send(f'You have {result[0]} XP')
