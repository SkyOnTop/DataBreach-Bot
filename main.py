'''
This code might be hard to read because I'm more accustomed to higher-level languages with different paradigms.
- Made by reversesxvm on discord, you are welcome to reach out if you need anything.
'''

import discord, sqlite3, os
from discord.ext import commands
from config import BOT_TOKEN

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.executescript('''
    CREATE TABLE IF NOT EXISTS whitelist (user_id INTEGER PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS settings (user_id INTEGER PRIMARY KEY, hidden_mode INTEGER);
    CREATE TABLE IF NOT EXISTS usage_stats (
        command TEXT PRIMARY KEY,
        uses INTEGER DEFAULT 0
    );
''')
conn.commit()

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    await load_cogs()
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds')
    print(f'Discord API version: {discord.__version__}')
    
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for data breaches"))
    
    print('Bot is ready!')

bot.run(BOT_TOKEN)