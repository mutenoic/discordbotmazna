import discord
from discord.ext import commands
from discord.ui import Button, View

# Ensure ButtonStyle is imported correctly
ButtonStyle = discord.ButtonStyle

# Import the bot from the configuration file
from config import bot

# Define the Player class
class Player:
    def __init__(self):
        self.hp = 100
        self.gold = 0
        self.inventory = []

# Define the Game class
class Game:
    def __init__(self):
        self.current_room = "start"
        self.rooms = {
            "start": {"description": "You are at the entrance of a dark dungeon.", "options": {"Go left": "left_room", "Go right": "right_room"}},
            "left_room": {"description": "You are in a room with a spooky ghost.", "options": {"Go back": "start"}},
            "right_room": {"description": "You find a room filled with treasure!", "options": {"Go back": "start"}}
        }

# Define the View for the game
class GameView(View):
    def __init__(self, game, player):
        super().__init__(timeout=180)  # Timeout for button interaction
        self.game = game
        self.player = player

    async def on_timeout(self):
        print("The game has timed out.")

# Define the Button for directions
class DirectionButton(Button):
    def __init__(self, label, destination, game, player):
        super().__init__(label=label, style=ButtonStyle.primary)  # Correctly reference ButtonStyle
        self.destination = destination
        self.game = game
        self.player = player

    async def callback(self, interaction):
        self.game.current_room = self.destination
        await interaction.response.edit_message(content=self.game.rooms[self.destination]['description'], view=GameView(self.game, self.player))
        await interaction.followup.send(f'You moved to {self.destination}.', ephemeral=True)

# Define the command to start the game
@bot.tree.command(name="startgame", description="Start a text-based adventure game.")
async def start_game(interaction: discord.Interaction):
    game = Game()
    player = Player()
    view = GameView(game, player)
    initial_text = game.rooms[game.current_room]['description']
    for option, destination in game.rooms[game.current_room]['options'].items():
        view.add_item(DirectionButton(option, destination, game, player))
    await interaction.response.send_message(initial_text, view=view)
