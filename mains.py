import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
last_status_message = None
last_status_message_id = None
last_update_time = None

def save_message_id(message_id):
    """Save the last status message ID to a file for persistence."""
    with open("last_status_message_id.txt", "w") as f:
        f.write(str(message_id))


# Load environment token
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Setup logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

CHANNEL_ID = 1381266422600040478

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    update_gtstatus.start()

@bot.command()
async def dm(ctx, *, msg):
    if ctx.message.mentions:
        user = ctx.message.mentions[0]
        await user.send(f"da {msg}")
        await ctx.send(f"✅ DM sent to {user.mention}")
    else:
        await ctx.send("❗ Tag seseorang untuk mengirim DM. Contoh: !dm @user pesanmu")

@bot.command()
async def reply(ctx):
    await ctx.reply("📬 This is a reply to your DM!")

@bot.command()
async def gtstatus(ctx):
    """Menampilkan status Growtopia saat ini (manual)."""
    url = "https://www.growtopiagame.com/detail"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            online = data.get("online_user", "N/A")
            await ctx.send(f"🌐 Jumlah pemain online saat ini: **{online}**")
        else:
            await ctx.send(f"❌ Gagal mengambil data: Status code {response.status_code}")
    except Exception as e:
        await ctx.send(f"⚠️ Terjadi error: {e}")

@tasks.loop(seconds=10)
async def update_gtstatus():
    global last_status_message_id, last_status_message, last_update_time

    url = "https://www.growtopiagame.com/detail"
    headers = {"User-Agent": "Mozilla/5.0"}

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❗ Channel tidak ditemukan.")
        return

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            online = int(data.get("online_user", 0))

            status = "Server is Down" if online <= 10 else data.get("status", "IS UP")

            now = datetime.now()
            seconds_ago = 0 if last_update_time is None else int((now - last_update_time).total_seconds())
            last_update_time = now

            # Emoji
            emoji1 = "<a:gummy:1381593596225917051>"
            emoji2 = "<a:gumm:1381593571257356338>"
            emoji3 = "<a:Load:1381591511132540989>"
            emoji4 = "<a:teasip:1381592970687549470>"
            emoji5 = "<a:alarm:1381734850700247070>"

            # Embed
            embed = discord.Embed(
                title=f"{emoji1} Growtopia Status Update {emoji2}",
                description="\n\n",
                color=discord.Color.blue()
            )

            embed.add_field(name=f"{emoji3} Status", value=f"**{status}**", inline=False)
            embed.add_field(name=f"{emoji4} Online Players", value=f"**{online}**", inline=False)
            embed.set_footer(
                text=f"Last Update: {seconds_ago} Seconds Ago",
                icon_url="https://cdn.discordapp.com/emojis/1381734850700247070.gif?size=96&quality=lossless"
            )

            if last_status_message is None:
                sent = await channel.send(embed=embed)
                last_status_message = sent
                last_status_message_id = sent.id
                save_message_id(sent.id)
            else:
                try:
                    await last_status_message.edit(embed=embed)
                except discord.NotFound:
                    sent = await channel.send(embed=embed)
                    last_status_message = sent
                    last_status_message_id = sent.id
                    save_message_id(sent.id)
        else:
            await channel.send(f"❌ Gagal mengambil data: Status code {response.status_code}")
    except Exception as e:
        await channel.send(f"⚠️ Terjadi error saat mengambil data: `{e}`")

    print("🔄 GT Status update task executed.")


# Jalankan bot
bot.run(token, log_handler=handler, log_level=logging.DEBUG)
