from main import random, asyncio
from config import bot
from yt_dlp import YoutubeDL
from src import get_info
from typing import Union
from config import bot



@bot.tree.command(
    name="guess",
    description="Play a number guessing game. The bot will generate a random number between 1 and 100, and you have to guess it.",
)
async def number_guessing_game(ctx):
    number_to_guess = random.randint(1, 100)
    attempts = 0
    max_attempts = 5

    await ctx.reply("I've picked a number between 1 and 100. Try to guess it!")

    while attempts < max_attempts:
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()

        try:
            guess = await bot.wait_for("message", check=check, timeout=30.0)
            guess = int(guess.content)

            if guess == number_to_guess:
                await ctx.reply(f"Congratulations! You guessed the number {number_to_guess} correctly!")
                return
            elif guess < number_to_guess:
                await ctx.reply("Too low! Try guessing higher.")
            else:
                await ctx.reply("Too high! Try guessing lower.")

            attempts += 1
        except asyncio.TimeoutError:
            await ctx.reply("Sorry, you took too long to guess. The number was {number_to_guess}.")
            return

    await ctx.reply(f"You've used up all your attempts! The number was {number_to_guess}.")


@bot.tree.command(
    name="quiz",
    description="Play a trivia quiz game. Answer questions by selecting the correct option.",
)
async def trivia_quiz(ctx):
    questions = [
        {
            "question": "What is the capital of France?",
            "options": ["London", "Paris", "Berlin", "Rome"],
            "answer": "Paris",
        },
        {
            "question": "Who wrote 'Romeo and Juliet'?",
            "options": ["William Shakespeare", "Jane Austen", "Charles Dickens", "Leo Tolstoy"],
            "answer": "William Shakespeare",
        },
        {
            "question": "What is the chemical symbol for water?",
            "options": ["H2O", "CO2", "CH4", "NaCl"],
            "answer": "H2O",
        },
    ]

    score = 0

    await ctx.reply("Welcome to the trivia quiz! Get ready to answer some questions.")

    for question in questions:
        options = "\n".join(
            [f"{i}. {option}" for i, option in enumerate(question["options"], start=1)])
        await ctx.reply(f"{question['question']}\n{options}")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit() and 1 <= int(message.content) <= len(question["options"])

        try:
            answer = await bot.wait_for("message", check=check, timeout=30.0)
            answer = int(answer.content)

            if question["options"][answer - 1] == question["answer"]:
                await ctx.reply("Correct answer!")
                score += 1
            else:
                await ctx.reply("Wrong answer!")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! Moving to the next question.")

    await ctx.reply(f"Quiz finished! Your score: {score}/{len(questions)}.")


@bot.tree.command(
    name="hangman",
    description="Play a game of Hangman. Try to guess the word within a limited number of attempts.",
)
async def hangman(ctx):
    words = ["apple", "banana", "cherry", "orange", "strawberry", "grape"]
    word_to_guess = random.choice(words)
    guessed_letters = []
    attempts = 6  # Number of attempts allowed
    revealed_word = ["_" if letter.isalpha(
    ) else letter for letter in word_to_guess]

    await ctx.reply("Welcome to Hangman! Try to guess the word by typing a letter.")

    while attempts > 0:
        hangman_display = f"{' '.join(revealed_word)}\n"
        hangman_display += "Guessed Letters: " + \
            ", ".join(guessed_letters) + "\n"
        hangman_display += f"Attempts Remaining: {attempts}\n"
        hangman_display += hangman_art(6 - attempts)  # Display Hangman art
        await ctx.reply(hangman_display)

        def check(message):
            return (
                message.author == ctx.author
                and message.channel == ctx.channel
                and message.content.isalpha()
                and len(message.content) == 1
            )

        try:
            guess = await bot.wait_for("message", check=check, timeout=30.0)
            guess = guess.content.lower()

            if guess in guessed_letters:
                await ctx.reply("You've already guessed that letter. Try another one.")
                continue

            guessed_letters.append(guess)

            if guess in word_to_guess:
                for i, letter in enumerate(word_to_guess):
                    if letter == guess:
                        revealed_word[i] = guess
                if "_" not in revealed_word:
                    await ctx.reply("Congratulations! You've guessed the word: " + word_to_guess)
                    return
                await ctx.reply("Correct guess!")
            else:
                attempts -= 1
                await ctx.reply(f"Incorrect guess! Attempts remaining: {attempts}")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The word was: " + word_to_guess)
            return

    await ctx.reply("You've used up all your attempts! The word was: " + word_to_guess)


def hangman_art(wrong_attempts):
    hangman_parts = [
        "  O  ",
        " \|/ ",
        "  |  ",
        " / \ ",
    ]
    hangman_display = ""
    for i in range(wrong_attempts):
        hangman_display += hangman_parts[i] + "\n"
    return hangman_display
