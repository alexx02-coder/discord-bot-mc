from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

keep_alive()
TOKEN = os.environ["TOKEN"]
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise RuntimeError("TOKEN manquant dans les variables d'environnement")
SERVER_IP = "Mys_Team.aternos.me"
CHANNEL_ID = 1484083970726691017

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

message_id = None

def get_status():
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = server.status()
        return True, status.players.online, status.players.max
    except:
        return False, 0, 0

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    update_status.start()

@tasks.loop(seconds=60)
async def update_status():
    global message_id
    channel = bot.get_channel(CHANNEL_ID)

    online, players, max_players = get_status()

    if online:
        content = f"🟢 Serveur en ligne\n👥 {players}/{max_players} joueurs"
    else:
        content = "🔴 Serveur hors ligne"

    if message_id is None:
        msg = await channel.send(content)
        message_id = msg.id
    else:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(content=content)
        except:
            msg = await channel.send(content)
            message_id = msg.id

@bot.command()
async def joueurs(ctx):
    online, players, max_players = get_status()

    if online:
        await ctx.send(f"👥 {players}/{max_players} joueurs")
    else:
        await ctx.send("🔴 Serveur hors ligne")

bot.run(TOKEN)

