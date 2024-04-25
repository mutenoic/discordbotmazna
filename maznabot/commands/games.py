import discord
from discord.ext import commands
from discord.ui import Button, View

ButtonStyle = discord.ButtonStyle

# Assuming 'bot' is imported from your config file
from config import bot

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
            "start": {
                "description": "You are at the entrance of a dark, echoing dungeon.",
                "options": {"Go left": "left_room", "Go right": "right_room"}
            },
            "left_room": {
                "description": "You are in a cold, dimly lit room. A ghostly figure looms near...",
                "options": {"Talk to the ghost": "ghost_story", "Go back": "start"},
                "event": "ghost_encounter"
            },
            "ghost_story": {
                "description": "The ghost whispers of hidden treasures and forgotten lore.",
                "options": {"Thank the ghost": "left_room"},
                "event": "resolve_ghost"
            },
            "right_room": {
                "description": "Gold coins glimmer in the torchlight, but danger lurks nearby.",
                "options": {"Gather gold": "treasure", "Go back": "start"}
            },
            "treasure": {
                "description": "As you gather gold, a trapdoor swings open beneath you!",
                "options": {"Explore below": "secret_room", "Climb out": "right_room"},
                "event": "fall_trap"
            },
            "secret_room": {
                "description": "You've discovered a secret library. Ancient books line the walls.",
                "options": {"Read a mysterious tome": "book_event", "Return above": "right_room"},
                "event": "library_found"
            },
            "book_event": {
                "description": "The tome reveals the path to a hidden exit!",
                "options": {"Use the secret exit": "end_game"},
                "event": "secret_path"
            },
            "end_game": {
                "description": "You've escaped the dungeon with treasures and tales to tell!",
                "options": {"Play again": "start"},
                "event": "game_won"
            }
        }
class GameView(View):
    def __init__(self, game, player):
        super().__init__(timeout=180)
        self.game = game
        self.player = player
        self.update_view()

    def update_view(self):
        self.clear_items()  # Clear existing buttons
        room = self.game.rooms[self.game.current_room]
        for option, destination in room['options'].items():
            self.add_item(DirectionButton(option, destination, self.game, self.player))

    async def on_timeout(self):
        print("The game has timed out.")

class DirectionButton(Button):
    def __init__(self, label, destination, game, player):
        super().__init__(label=label, style=ButtonStyle.primary)
        self.destination = destination
        self.game = game
        self.player = player

    async def callback(self, interaction):
        self.game.current_room = self.destination
        room_description = self.game.rooms[self.destination]['description']
        # Reset view based on new room options
        view = GameView(self.game, self.player)
        await interaction.response.edit_message(content=room_description, view=view)
        await interaction.followup.send(f"You moved to {self.destination}.", ephemeral=True)

@bot.tree.command(name="startgame", description="Start a text-based adventure game.")
async def start_game(interaction: discord.Interaction):
    game = Game()
    player = Player()
    view = GameView(game, player)
    initial_text = game.rooms[game.current_room]['description']
    await interaction.response.send_message(initial_text, view=view)