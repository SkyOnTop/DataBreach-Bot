import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

class HiddenMode(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"{'Enable' if i else 'Disable'} Hidden Mode", description=f"Messages will be {'ephemeral (visible only to you)' if i else 'visible to everyone'}.", value=str(i)) for i in range(2)]
        super().__init__(placeholder="Choose Hidden Mode", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        hidden_mode = self.values[0] == "1"
        c.execute("INSERT OR REPLACE INTO settings (user_id, hidden_mode) VALUES (?, ?)", (interaction.user.id, int(hidden_mode)))
        conn.commit()
        await interaction.response.send_message(f"Hidden mode has been {'enabled' if hidden_mode else 'disabled'}.", ephemeral=True)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="Configure bot settings")
    async def settings(self, interaction: discord.Interaction):
        await interaction.response.send_message("Configure your settings below:", view=discord.ui.View().add_item(HiddenMode()), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot))