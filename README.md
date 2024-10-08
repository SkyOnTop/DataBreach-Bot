# DataBreach V1 Discord Bot

I decided to release this since it’s been sitting on my computer for a while, and I just came across it again—so I figured, why not share it?

This Discord bot provides data breach search functionality using the Snusbase API.

## Setup Instructions

1. **Clone the repository**
   ```
   git clone https://github.com/SkyOnTop/DataBreach-Bot.git
   cd DataBreach-Bot
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Set up the database**
   - The bot uses SQLite, which will be created automatically when the bot runs.

4. **Configure the bot**
   - Rename `config.example.py` to `config.py`
   - Edit `config.py` and add your Discord bot token and Snusbase API key

5. **Run the bot**
   ```
   python main.py
   ```

## Features

- Search Snusbase for data breaches
- IP WHOIS lookup
- Admin commands for managing whitelist and generating keys
- User settings for hidden searching mode

## Commands

- `/search`: Search Snusbase for a term
- `/ipwhois`: Get information on an IP address
- `/settings`: Configure bot settings
- `/whitelist`: (Admin) Add or remove a member from the whitelist
- `/genkey`: (Admin) Generate whitelist keys
- `/redeem`: Redeem a key to gain access to the bot's features
- `/buy`: Get information on purchasing whitelist access

## Support

For support, please contact reversesxvm on Discord. This bot will not be updated unless heavily requested.
