import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import requests
import json
import tempfile
import os
import re
from typing import List, Dict, Any
from config import SNUSBASE_API_KEY

conn = sqlite3.connect('database.db')
c = conn.cursor()

API_KEY, BASE_URL = SNUSBASE_API_KEY, 'https://api.snusbase.com/v3/search'

def snusbasev1(search_type: str, term: str) -> Dict[str, Any]:
    headers = {'Auth': API_KEY, 'Content-Type': 'application/json'}
    try:
        response = requests.post(BASE_URL, json={'type': search_type, 'term': term}, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        return {"error": str(error)}

def snusbasev2(username: str) -> List[str]:
    headers = {'Auth': API_KEY, 'Content-Type': 'application/json'}
    search_data = {'type': 'username', 'term': username}
    try:
        response = requests.post(BASE_URL, json=search_data, headers=headers)
        response.raise_for_status()
        results = response.json()
        return [entry.get('password', 'No password found') for entry in results.get('results', []) if entry.get('password')]
    except Exception as error:
        print(error)
        return []

class SearchModal(discord.ui.Modal):
    def __init__(self, term: str, results: List[Dict[str, Any]], hidden_mode: bool):
        super().__init__(title="Enter string to search")
        self.term, self.results, self.hidden_mode = term, results, hidden_mode
        self.string_input = discord.ui.TextInput(label="Search Term", placeholder="Enter string to search...")
        self.add_item(self.string_input)

    async def on_submit(self, interaction: discord.Interaction):
        search_term = self.string_input.value.lower()
        filtered_results = [entry for entry in self.results if any(search_term in str(value).lower() for value in entry.values())]

        if not filtered_results:
            await interaction.response.send_message(f"<:Pixel_Cross_shadow:1282044427522543626> No results found for `{search_term}`.", ephemeral=self.hidden_mode)
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as temp_file:
            json.dump(filtered_results, temp_file, indent=4)
            temp_file_path = temp_file.name

        embed = discord.Embed(
            description=f":white_check_mark: Results for `{search_term}`",
            color=discord.Color.light_grey()
        )
        embed.set_author(name="DataBreach v2", icon_url="https://futurealts.xyz/S%20(2).png")
        await interaction.response.send_message(embed=embed, file=discord.File(temp_file_path, filename='filtered_results.json'), ephemeral=self.hidden_mode)

        os.remove(temp_file_path)

class SearchDropdown(discord.ui.Select):
    def __init__(self, term: str, results: List[Dict[str, Any]], hidden_mode: bool, interaction_user_id: int):
        super().__init__(placeholder="Choose search type", min_values=1, max_values=1, options=[discord.SelectOption(label=l, description=f"Search by {l.lower()}") for l in ["String", "Database"]])
        self.term, self.results, self.hidden_mode, self.interaction_user_id = term, results, hidden_mode, interaction_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user_id:
            await interaction.response.send_message("You are not authorized to interact with this.", ephemeral=True)
            return
        await interaction.response.send_modal(SearchModal(self.term, self.results, self.hidden_mode)) if self.values[0] == "String" else interaction.response.edit_message(view=DatabaseView(self.term, self.results, interaction, self.hidden_mode, self.interaction_user_id))

class DatabaseView(discord.ui.View):
    def __init__(self, term, results, interaction, hidden_mode, interaction_user_id):
        super().__init__()
        self.term, self.page, self.results, self.interaction, self.hidden_mode, self.interaction_user_id = term, 0, results, interaction, hidden_mode, interaction_user_id
        self.filtered_databases = self.filter_databases()
        self.update_dropdown()

    def filter_databases(self):
        db_count = {}
        for entry in self.results:
            db = entry.get('db')
            if db: db_count[db] = db_count.get(db, 0) + 1
        return {db: count for db, count in db_count.items() if count > 1}

    def update_dropdown(self):
        self.clear_items()
        start, end = self.page * 25, (self.page + 1) * 25
        paginated_databases = sorted(self.filtered_databases.items(), key=lambda x: x[1], reverse=True)[start:end]
        self.add_item(DatabaseDropdown(paginated_databases, self.page, self.term, self.interaction, self.results, self.hidden_mode, self.interaction_user_id))
        self.add_item(PreviousButton(self, disabled=self.page == 0, interaction_user_id=self.interaction_user_id))
        self.add_item(NextButton(self, disabled=len(self.filtered_databases) <= end, interaction_user_id=self.interaction_user_id))

class DatabaseDropdown(discord.ui.Select):
    def __init__(self, paginated_databases, page, term, interaction, all_results, hidden_mode, interaction_user_id):
        super().__init__(placeholder="Choose a database", min_values=1, max_values=1, options=[discord.SelectOption(label=f"{db} ({count} results)", value=db) for db, count in paginated_databases])
        self.paginated_databases, self.page, self.term, self.interaction, self.all_results, self.hidden_mode, self.interaction_user_id = paginated_databases, page, term, interaction, all_results, hidden_mode, interaction_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user_id:
            await interaction.response.send_message("You are not authorized to interact with this.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=self.hidden_mode)
        selected_db = self.values[0]
        filtered_results = [entry for entry in self.all_results if entry.get('db') == selected_db]
        if not filtered_results:
            await interaction.followup.send(f"<:Pixel_Cross_shadow:1282044427522543626> No results found for database `{selected_db}`.", ephemeral=self.hidden_mode)
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as temp_file:
            json.dump(filtered_results, temp_file, indent=4)
            temp_file_path = temp_file.name
        embed = discord.Embed(description=f":white_check_mark: Results for `{self.term}` in `{selected_db}`", color=discord.Color.light_grey())
        embed.set_author(name="DataBreach v2", icon_url="https://futurealts.xyz/S%20(2).png")
        await interaction.followup.send(embed=embed, file=discord.File(temp_file_path, filename='filtered_results.json'), ephemeral=self.hidden_mode)
        os.remove(temp_file_path)

class PreviousButton(discord.ui.Button):
    def __init__(self, view, disabled=False, row=1, interaction_user_id=None):
        super().__init__(label="Previous", style=discord.ButtonStyle.primary, disabled=disabled, row=row)
        self.view_instance, self.interaction_user_id = view, interaction_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user_id:
            await interaction.response.send_message("You are not authorized to interact with this.", ephemeral=True)
            return
        if self.view_instance.page > 0:
            self.view_instance.page -= 1
            self.view_instance.update_dropdown()
            await interaction.response.edit_message(view=self.view_instance)

class NextButton(discord.ui.Button):
    def __init__(self, view, disabled=False, row=1, interaction_user_id=None):
        super().__init__(label="Next", style=discord.ButtonStyle.primary, disabled=disabled, row=row)
        self.view_instance, self.interaction_user_id = view, interaction_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.interaction_user_id:
            await interaction.response.send_message("You are not authorized to interact with this.", ephemeral=True)
            return
        if len(self.view_instance.filtered_databases) > (self.view_instance.page + 1) * 25:
            self.view_instance.page += 1
            self.view_instance.update_dropdown()
            await interaction.response.edit_message(view=self.view_instance)

class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="search", description="Search Snusbase for a term")
    @app_commands.describe(term="The term to search for", search_type="The type of search to perform")
    @app_commands.choices(search_type=[app_commands.Choice(name=n, value=n) for n in ["username", "email", "password", "hash", "name", "domain"]])
    async def search(self, interaction: discord.Interaction, term: str, search_type: app_commands.Choice[str] = None):
        whitelist = {str(row[0]): True for row in c.execute("SELECT user_id FROM whitelist")}
        if str(interaction.user.id) not in whitelist:
            await interaction.response.send_message("<:Pixel_Cross_shadow:1282044427522543626> You are not whitelisted. Please buy a key with `/buy`.", ephemeral=True)
            return
        hidden_mode = (c.execute("SELECT hidden_mode FROM settings WHERE user_id = ?", (interaction.user.id,)).fetchone() or [0])[0] == 1
        await interaction.response.defer(ephemeral=hidden_mode)
        search = search_type.value if search_type else 'email' if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', term) else 'username'
        try:
            search_results = snusbasev1(search, term)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w') as temp_file:
                json.dump(search_results, temp_file, indent=4)
                temp_file_path = temp_file.name
        except Exception as error:
            await interaction.followup.send(error, ephemeral=hidden_mode)
            return
        if not isinstance(search_results, dict) or 'results' not in search_results or not isinstance(search_results['results'], list):
            await interaction.followup.send("<:Pixel_Cross_shadow:1282044427522543626> Search results were not in the expected format.", ephemeral=hidden_mode)
            return
        results = search_results['results']
        if not results:
            await interaction.followup.send("<:Pixel_Cross_shadow:1282044427522543626> No results found.", ephemeral=hidden_mode)
            return
        try:
            embed = discord.Embed(description=f":white_check_mark: Here are your search results for `{term}`", color=discord.Color.light_grey())
            embed.set_author(name="DataBreach v2", icon_url="https://futurealts.xyz/S%20(2).png")
            view = discord.ui.View().add_item(SearchDropdown(term, results, hidden_mode, interaction.user.id))
            await interaction.followup.send(embed=embed, view=view, ephemeral=hidden_mode, file=discord.File(temp_file_path, filename='results.json'))
            os.remove(temp_file_path)
        except Exception as error:
            await interaction.followup.send(error, ephemeral=hidden_mode)

    @commands.command(name="lf")
    async def find_passwords(self, ctx, username: str):
        whitelist = {str(row[0]): True for row in c.execute("SELECT user_id FROM whitelist")}
        if str(ctx.author.id) not in whitelist:
            await ctx.reply("<:Pixel_Cross_shadow:1282044427522543626> You are not whitelisted. Please buy a key with `/buy`.")
            return
        passwords = snusbasev2(username)
        if not passwords:
            await ctx.reply(f"No passwords found for `{username}`.")
            return
        password_list = '\n'.join(passwords)
        formatted_passwords = f"```\n{password_list}\n```"
        if len(formatted_passwords) > 4000:
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt', encoding='utf-8') as temp_file:
                temp_file.write(password_list)
                temp_file_path = temp_file.name
            embed = discord.Embed(description=f":white_check_mark: Here are your search results for {username}", color=discord.Color.light_grey())
            embed.set_footer(text=f"These are passwords for the username {username}")
            embed.set_author(name="DataBreach v2", icon_url="https://futurealts.xyz/S%20(2).png")
            await ctx.reply(embed=embed, file=discord.File(temp_file_path, f'{username}_passwords.txt'))
            os.remove(temp_file_path)
        else:
            embed = discord.Embed(description=f":white_check_mark: Here are your search results for {username}\n\n{formatted_passwords}", color=discord.Color.light_grey())
            embed.set_author(name="DataBreach v2", icon_url="https://futurealts.xyz/S%20(2).png")
            embed.set_footer(text=f"These are passwords for the username {username}")
            await ctx.reply(embed=embed)

    @app_commands.command(name="ipwhois", description="Get information on an IP address")
    @app_commands.describe(ip_address="The IP address to search for")
    async def ipwhois(self, interaction: discord.Interaction, ip_address: str):
        whitelist = {str(row[0]): True for row in c.execute("SELECT user_id FROM whitelist")}
        if str(interaction.user.id) not in whitelist:
            await interaction.response.send_message("<:Pixel_Cross_shadow:1282044427522543626> You are not whitelisted. Please buy a key with `/buy`.", ephemeral=True)
            return
        hidden_mode = (c.execute("SELECT hidden_mode FROM settings WHERE user_id = ?", (interaction.user.id,)).fetchone() or [0])[0] == 1
        api_url = f"https://ipwhois.app/json/{ip_address}"
        try:
            response = requests.get(api_url)
            data = response.json()
            if not data.get("success", True):
                await interaction.response.send_message(f"Error: {data.get('message', 'unable to fetch IP information.')}", ephemeral=hidden_mode)
                return
            embed = discord.Embed(title=f"📌 IP Information For {ip_address.lower()}", color=discord.Color.light_grey())
            for field in ["ip", "country", "region", "city", "isp", "org", "asn"]:
                embed.add_field(name=field.capitalize(), value=data.get(field, "n/a"), inline=True)
            embed.set_author(name="DataBreach v2", icon_url="https://futurealts.xyz/S%20(2).png")
            embed.set_thumbnail(url="https://futurealts.xyz/S%20(2).png")
            await interaction.response.send_message(embed=embed, ephemeral=hidden_mode)
        except Exception as error:
            await interaction.response.send_message(f"An error occurred: {str(error).lower()}", ephemeral=hidden_mode)

async def setup(bot):
    await bot.add_cog(Search(bot))