import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import string
import tempfile
import os
from config import ADMIN_IDS

conn = sqlite3.connect('database.db')
c = conn.cursor()

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whitelist", description="Add or remove a member from the whitelist")
    @app_commands.describe(action="Specify 'add' to add or 'remove' to remove a member", member="The member to add or remove from the whitelist")
    async def whitelist(self, interaction: discord.Interaction, action: str, member: discord.Member):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("<:Pixel_Cross_shadow:1282044427522543626> Only admins can use this command!", ephemeral=True)
            return
        action = action.lower()
        if action not in ["add", "remove"]:
            await interaction.response.send_message("<:Pixel_Cross_shadow:1282044427522543626> Invalid action! Use `add` or `remove`.", ephemeral=True)
            return
        c.execute("INSERT OR REPLACE INTO whitelist (user_id) VALUES (?)", (member.id,))
        conn.commit()
        embed = discord.Embed(description=f"<:Pixel_checkmark_shadow:1282044324313432136> {member.mention} has been {'added to' if action == 'add' else 'removed from'} the whitelist.", color=discord.Color.light_grey() if action == "add" else discord.Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="genkey", description="Generate a specified number of keys")
    @app_commands.describe(amount="The number of keys to generate")
    async def genkey(self, interaction: discord.Interaction, amount: int):
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("<:Pixel_Cross_shadow:1282044427522543626> Only admins can use this command!", ephemeral=True)
            return
        new_keys = [''.join(random.choices(string.ascii_letters + string.digits, k=16)) for _ in range(amount)]
        try:
            c.executemany("INSERT OR REPLACE INTO keys (key) VALUES (?)", [(key,) for key in new_keys])
            conn.commit()
        except Exception as error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w') as temp_file:
            temp_file.write('\n'.join(new_keys))
            temp_file_path = temp_file.name
        await interaction.user.send("Here are your keys:", file=discord.File(temp_file_path, 'keys.txt'))
        os.remove(temp_file_path)
        await interaction.response.send_message(f"Successfully generated {amount} keys.", ephemeral=True)

    @app_commands.command(name="redeem", description="Redeem a key to gain access to the bot's features")
    @app_commands.describe(key="The key to redeem")
    async def redeem(self, interaction: discord.Interaction, key: str):
        keys = [row[0] for row in c.execute("SELECT key FROM keys")]
        if key in keys:
            c.execute("DELETE FROM keys WHERE key = ?", (key,))
            c.execute("INSERT OR REPLACE INTO whitelist (user_id) VALUES (?)", (interaction.user.id,))
            conn.commit()
            embed = discord.Embed(description=":white_check_mark: You have been added to the database. You may now use the commands for this bot!", color=discord.Color.light_grey())
        else:
            embed = discord.Embed(description="<:Pixel_Cross_shadow:1282044427522543626> Invalid key, make sure you entered the correct key.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase whitelist access")
    async def buy(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://databreachstore.mysellix.io/product/databreach-key")

async def setup(bot):
    await bot.add_cog(Admin(bot))