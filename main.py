import os
import asyncio
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from threading import Thread
import discord
from discord.ext import commands

# 1. SETUP DISCORD BOT (This keeps the green dot)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. LOGGING LOGIC
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1410458084874260592"))

def make_embed(payload):
    """Your original embed builder logic"""
    bot_name = payload.get("bot_name", "Unknown Bot")
    embed = discord.Embed(
        title="Command Triggered",
        description="A command or trigger was used in the server.",
        timestamp=datetime.now(timezone.utc),
        color=0x2F3136
    )
    embed.set_author(name=bot_name)
    embed.add_field(name="Command / Trigger", value=f"`{payload.get('command', 'unknown')}`", inline=True)
    embed.add_field(name="Who triggered it", value=f"{payload.get('username', 'Unknown')} (`{payload.get('user_id', 'unknown')}`)", inline=True)
    
    extra = payload.get("extra", {})
    if isinstance(extra, dict):
        for k, v in extra.items():
            embed.add_field(name=k, value=str(v)[:1024], inline=False)
    
    embed.set_footer(text=f"{os.getenv('BOT_DISPLAY_NAME', 'Logger')} • logged")
    return embed

@bot.event
async def on_ready():
    # This loads the 'commands_file.py'
    await bot.load_extension("commands_file")
    
    # Syncs your slash commands so they show up in Discord
    await bot.tree.sync()
    
    print(f'Logged in as {bot.user.name} and commands are loaded!')


@bot.tree.command(name="ping", description="Test if the bot is alive")
async def ping(interaction: discord.Interaction):
    # For slash commands, you MUST use interaction.response.send_message
    await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms")

# 3. WEB SERVER (For Render and the Notify API)
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is Online and Logger is running."

@app.route("/notify", methods=["POST"])
def notify():
    payload = request.get_json()
    if not payload or "command" not in payload:
        return jsonify({"error": "invalid payload"}), 400

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        # This sends the log using the bot's live connection
        bot.loop.create_task(channel.send(embed=make_embed(payload)))
        return jsonify({"ok": True}), 200
    return jsonify({"error": "channel not found"}), 500

# 4. STARTUP
def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    # Start the web server thread
    Thread(target=run_flask).start()
    # Run the Discord bot (This is what makes it green)
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
