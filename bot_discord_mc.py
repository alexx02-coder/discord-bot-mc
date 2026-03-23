from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from discord import app_commands
import os
import concurrent.futures

keep_alive()

TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise RuntimeError("TOKEN manquant dans les variables d'environnement")

SERVER_IP = "Mys_Team.aternos.me"
CHANNEL_ID = 1484083970726691017

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

message_id = None
last_state = None

# Thread pool pour éviter les blocages
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def safe_ping(server):
    try:
        return server.ping()
    except:
        return None

def safe_status(server):
    try:
        return server.status()
    except:
        return None

def get_status():
    try:
        server = JavaServer.lookup(SERVER_IP)

        # Ping avec timeout
        future_ping = executor.submit(safe_ping, server)
        latency = future_ping.result(timeout=1)

        if latency is None:
            return "transition", 0, 0

        # Status avec timeout
        future_status = executor.submit(safe_status, server)
        status = future_status.result(timeout=1)

        if status is None:
            return "transition", 0, 0

        return True, status.players.online, status.players.max

    except Exception as e:
        print("Erreur get_status :", e)
        return False, 0, 0


@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    await tree.sync()
    print("Slash commands synchronisées")
    update_status.start()


@tasks.loop(seconds=750)
async def update_status():
    global message_id, last_state

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Salon introuvable, nouvelle tentative…")
        return

    online, players, max_players = get_status()

    # Détermination du message principal
    if online is True:
        content = f"🟢 Serveur en ligne\n👥 {players}/{max_players} joueurs"
    elif online == "transition":
        content = "🟡 Serveur en transition… (lag / démarrage)"
    else:
        content = "🔴 Serveur hors ligne"

    # Détection changement d'état
    if last_state is None:
        last_state = online
    else:
        if online != last_state:
            if online is True:
                await channel.send("🟢 **Le serveur vient de s'allumer !**")
            elif online is False:
                await channel.send("🔴 **Le serveur vient de s'éteindre !**")
            last_state = online

    # Gestion du message principal
    if message_id is None:
        try:
            msg = await channel.send(content)
            message_id = msg.id
            print("Message créé :", message_id)
        except Exception as e:
            print("Erreur lors de l'envoi du message :", e)
        return

    try:
        msg = await channel.fetch_message(message_id)
        await msg.edit(content=content)
        print("Message mis à jour")
    except discord.NotFound:
        print("Message introuvable, recréation…")
        msg = await channel.send(content)
        message_id = msg.id
    except Exception as e:
        print("Erreur update_status :", e)


# ============================
#     SLASH COMMANDS
# ============================

@tree.command(name="serveur", description="Affiche l'état du serveur Minecraft")
async def serveur(interaction: discord.Interaction):
    await interaction.response.defer()

    online, players, max_players = get_status()

    if online is True:
        await interaction.followup.send(
            f"🟢 Serveur en ligne\n👥 {players}/{max_players} joueurs"
        )
    elif online == "transition":
        await interaction.followup.send("🟡 Serveur en transition… (lag / démarrage)")
    else:
        await interaction.followup.send("🔴 Serveur hors ligne")


@tree.command(name="joueurs", description="Affiche le nombre de joueurs connectés")
async def joueurs(interaction: discord.Interaction):
    await interaction.response.defer()

    online, players, max_players = get_status()

    if online is True:
        await interaction.followup.send(
            f"👥 {players}/{max_players} joueurs"
        )
    elif online == "transition":
        await interaction.followup.send("🟡 Serveur en transition… (lag / démarrage)")
    else:
        await interaction.followup.send("🔴 Serveur hors ligne")


bot.run(TOKEN)




