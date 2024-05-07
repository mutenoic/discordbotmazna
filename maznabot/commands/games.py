import discord
from discord.ext import commands
from discord.ui import Button, View

ButtonStyle = discord.ButtonStyle
from config import bot  # Assuming 'bot' is already configured

class Player:
    def __init__(self):
        self.hp = 100
        self.gold = 0
        self.inventory = []

class Game:
    def __init__(self):
        self.current_room = "start"
        self.rooms = {
            "start": {
                "description": "You are at the entrance of a dark, echoing dungeon. A flickering torch casts long shadows.",
                "options": {"Go left": "left_room", "Go right": "right_room", "Enter the cavern": "cavern_entrance"},
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232984621948469259/mikhail-p-enterthedungeon.png?ex=662b71e9&is=662a2069&hm=dca01c29fa4940d6fbeb1d70bd4f0f5873f1cdb44c898592b4ed9b0200351860&"
            },
            "left_room": {
                "description": "You find yourself in a cold, dimly lit room. A ghostly figure looms near...",
                "options": {"Talk to the ghost": "ghost_story", "Go back": "start"},
                "event": "ghost_encounter",
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232984832292950087/91bd504225cc41958d1bae8145b9e83d.png?ex=662b721b&is=662a209b&hm=6e9aaee4a891e4c1ce4ddf853e9ed9c06a4ec9a18d55f6bc13e6587e831f165a&"
            },
            "ghost_story": {
                "description": "The ghost whispers of hidden treasures and forgotten lore.",
                "options": {"Thank the ghost": "left_room"},
                "event": "resolve_ghost",
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232985006146719799/Ghost-5e-Guide-1-950x650.png?ex=662b7245&is=662a20c5&hm=47d2866188fab321d41ce41cfca3098915a82b58d56fbb2ef6d75a9656897f42&"
            },
            "right_room": {
                "description": "Gold coins glimmer in the torchlight, but danger lurks nearby.",
                "options": {"Gather gold": "treasure", "Go back": "start"},
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232985170638803046/open-treasure-chest-filled-with-lot-gold-coins-medieval-dungeon_846485-37922.png?ex=662b726c&is=662a20ec&hm=26b68f83f48f5fc867a610c96df550cb24bc341e0c297890dd2c4f40b760d6ff&"
            },
            "treasure": {
                "description": "As you gather gold, a trapdoor swings open beneath you!",
                "options": {"Explore below": "secret_room", "Climb out": "right_room"},
                "event": "fall_trap",
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232988682978332712/InUxi-nOSCqa89zx-ZXKMg.png?ex=662b75b1&is=662a2431&hm=a8cdffba23730cf5ef9389cc7a4d352b7d1e40c44516626d541f4ba4542baf34&"
            },
            "secret_room": {
                "description": "You've discovered a secret library. Ancient books line the walls.",
                "options": {"Read a mysterious tome": "book_event", "Return above": "right_room"},
                "event": "library_found",
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232988384792936449/Library-1.png?ex=662b756a&is=662a23ea&hm=793238acd3e18e14546acb3507f689315dcf621b04951bff2bbb2189a116e54f&"
            },
            "book_event": {
                "description": "The tome reveals the path to a hidden exit!",
                "options": {"Use the secret exit": "end_game"},
                "event": "secret_path",
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232988221680521268/8eb1d66d-fd52-4537-aea1-c78ff4202b1b.png?ex=662b7543&is=662a23c3&hm=3c85cceadbdc28968f65e4a298377a36b4a342d94d764fa6577020f31fac008f&"
            },
            "end_game": {
                "description": "You've escaped the dungeon with treasures and tales to tell!",
                "options": {"Play again": "start"},
                "event": "game_won",
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232987970965999646/dnd-boulder-run.png?ex=662b7508&is=662a2388&hm=800474adc4f40d9853d74204a91f1cc262abf83892c963f9554e2f7074de4302&"
            },
            "cavern_entrance": {
                "description": "A large cavern opens up before you, filled with bioluminescent fungi and distant echoes.",
                "options": {"Explore deeper": "deep_cavern", "Go back": "start"},
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232987741348954122/opt__aboutcom__coeus__resources__content_migration__treehugger__images__2015__08__joseph-michael-glowworm-cave-photos-5-ea27eebbaab54a2e8be6e822bbf5fd4d.png?ex=662b74d1&is=662a2351&hm=bc2c665d12797a976283251d5ab225b638104811608139c74a73d096590c2fa0&"
            },
            "deep_cavern": {
                "description": "Deeper in the cavern, you encounter a sleeping dragon guarding a massive hoard of treasure.",
                "options": {"Sneak past the dragon": "dragon_hoard", "Retreat quietly": "cavern_entrance"},
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232987619307294740/1650144656668.png?ex=662b74b4&is=662a2334&hm=31676aa6915dcd740f7ad9da8842db00dec390b558e869195bc3f026bcbb88a1&"
            },
            "dragon_hoard": {
                "description": "You've managed to sneak past the dragon and now stand before an immense treasure.",
                "options": {"Take treasure and escape": "end_game", "Leave the treasure": "deep_cavern"},
                "image": "https://cdn.discordapp.com/attachments/1103536796119347300/1232987438125944872/treasure.png?ex=662b7489&is=662a2309&hm=2e5674033f61745a6832a12f6c7db7d9ee0916a320a0e1ac4c1d75f3eedf0be3&"
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
        room = self.game.rooms[self.destination]
        room_description = room['description']
        room_image = room.get('image', 'https://cdn.discordapp.com/attachments/1103536796119347300/1232987290125471785/8907c11ce7ec65fc6587a8a74c6d2ce3-d4n0uik.png?ex=662b7465&is=662a22e5&hm=601c12b286776621eccd420dc98976c0410f24bd2af9d20a15b3531dc883efba&')

        # Create an embed with the new room's description and image
        embed = discord.Embed(description=room_description)
        embed.set_image(url=room_image)
        view = GameView(self.game, self.player)

        # Update the message in place rather than sending a new message
        await interaction.response.edit_message(embed=embed, view=view)


@bot.tree.command(name="startgame", description="Start a text-based adventure game.")
async def start_game(interaction: discord.Interaction):
    game = Game()
    player = Player()
    view = GameView(game, player)
    initial_room = game.rooms[game.current_room]
    initial_embed = discord.Embed(description=initial_room['description'])
    initial_embed.set_image(url=f"http://example.com/path/to/images/{initial_room.get('image', 'default_image.jpg')}")
    await interaction.response.send_message(embed=initial_embed, view=view)
