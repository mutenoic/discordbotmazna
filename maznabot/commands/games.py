from main import random, discord, asyncio
from config import bot

@bot.tree.command(
    name="startgame",
    description="Start a text-based adventure game. Explore rooms, fight monsters, and collect treasures."
)
async def text_adventure_game(ctx: discord.Interaction):
    player_hp = 100
    player_gold = 0
    player_inventory = []

    game_map = {
        "start": {
            "description": "You find yourself in a dark and mysterious maze.",
            "exits": {"left": "trap_room", "right": "treasure_room"}
        },
        "trap_room": {
            "description": "You've entered a trap room. You are attacked by a giant spider!",
            "monster": "giant spider",
            "monster_hp": 50,
            "monster_attack": 20,
            "reward": {"gold": 50}
        },
        "treasure_room": {
            "description": "You've found a room filled with treasures!",
            "reward": {"gold": 100, "item": "magic sword"}
        }
    }

    current_room = "start"

    while True:
        message_content = game_map[current_room]["description"] + "\n"

        if "monster" in game_map[current_room]:
            monster_name = game_map[current_room]["monster"]
            monster_hp = game_map[current_room]["monster_hp"]
            monster_attack = game_map[current_room]["monster_attack"]

            # Fight the monster
            message_content += f"You encounter a {monster_name}!\n"

            # Battle logic
            while player_hp > 0 and monster_hp > 0:
                # Player attacks
                player_damage = random.randint(10, 20)
                monster_hp -= player_damage
                message_content += f"You attack the {monster_name} for {player_damage} damage!\n"

                if monster_hp <= 0:
                    break

                # Monster attacks
                monster_damage = random.randint(10, 20)
                player_hp -= monster_damage
                message_content += f"The {monster_name} attacks you for {monster_damage} damage!\n"

                if player_hp <= 0:
                    break

            # Check battle outcome
            if player_hp > 0:
                # Player wins
                message_content += f"You defeated the {monster_name}!\n"
                # Add reward to player
                player_gold += game_map[current_room]["reward"]["gold"]
            else:
                # Player loses
                message_content += "You were defeated by the monster. Game Over.\n"
                break

        # Check if the current room has a reward
        if "reward" in game_map[current_room]:
            # Add reward to player
            player_gold += game_map[current_room]["reward"]["gold"]
            if "item" in game_map[current_room]["reward"]:
                player_inventory.append(game_map[current_room]["reward"]["item"])

        # Display player stats
        message_content += f"Current Gold: {player_gold}\nInventory: {', '.join(player_inventory)}\n"

        # Check if the current room has exits
        if "exits" in game_map[current_room]:
            # Allow player to choose next room using buttons
            exits = game_map[current_room]["exits"]
            buttons = []
            for direction, room in exits.items():
                buttons.append(discord.ui.Button(style=discord.ButtonStyle.primary, label=direction.capitalize(), custom_id=room))

            # Create a view with buttons
            view = discord.ui.View()
            for button in buttons:
                view.add_item(button)

            message_content += "Where do you want to go?\n"

            # Send message with buttons
            message = await ctx.send(message_content, view=view)

            try:
                # Wait for user choice
                interaction = await bot.wait_for("button_click", check=lambda i: i.user == ctx.author and i.message == message, timeout=30)
                next_room = interaction.custom_id
                if next_room in exits.values():
                    current_room = next_room
                else:
                    await interaction.response.send_message("Invalid choice. Please choose again.")
            except asyncio.TimeoutError:
                await ctx.send("You took too long to decide. Game Over.")
                return

        # Check if player has won the game
        # End the game loop if necessary
        if current_room == "final_room":
            await ctx.send("Congratulations! You have reached the end of the dungeon.")
            break
