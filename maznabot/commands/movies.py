from main import random, asyncio
import sqlite3
from config import bot
import os


def generateDb():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS movies (title TEXT, year INTEGER)')
    conn.commit()
    conn.close()


@bot.command(
    name='list',
    description='List all movies in the database',
)
async def listAllMovies(ctx):
    generateDb()
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('SELECT * FROM movies')
    movies = c.fetchall()
    conn.close()
    if not movies:
        return await ctx.send('No movies in the database')
    movieList = []
    for movie in movies:
        movieList.append(f'{movie[0]} ({movie[1]})')
    return await ctx.send('\n'.join(movieList))


@bot.command(
    name='add',
    description='Add a movie to the database'
)
async def addMovie(ctx, title: str, year: int):
    generateDb()
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('INSERT INTO movies VALUES (?, ?)', (title, year))
    conn.commit()
    conn.close()
    return await ctx.send(f'{title} ({year}) added to the database')
