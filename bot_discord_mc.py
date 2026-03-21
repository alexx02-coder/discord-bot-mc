from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
import os

keep_alive()

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

        # Test rapide : le serveur répond-il au ping ?
        latency = server.ping()

        # Si le ping passe, on peut demander le status
        status = server.status()
        return True, status.players.online, status.players.max

    except Exception as e:
        print("Erreur get_status :", e)
        return False, 0, 0



@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    update_status.start()


@tasks.loop(seconds=240)
async def update_status():
    global message_id

    # Vérifier que le salon est accessible
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Salon introuvable, nouvelle tentative dans 200s…")
        return

    online, players, max_players = get_status()

    if online:
        content = f"🟢 Serveur en ligne\n👥 {players}/{max_players} joueurs"
    else:
        content = "🔴 Serveur hors ligne"

    # Si aucun message n'est enregistré → on en crée un
    if message_id is None:
        try:
            msg = await channel.send(content)
            message_id = msg.id
            print("Message créé :", message_id)
        except Exception as e:
            print("Erreur lors de l'envoi du message :", e)
        return

    # Sinon on essaie de modifier le message existant
    try:
        msg = await channel.fetch_message(message_id)
        await msg.edit(content=content)
        print("Message mis à jour")
    except discord.NotFound:
        # Le message n'existe plus → on en recrée un
        print("Message introuvable, recréation…")
        msg = await channel.send(content)
        message_id = msg.id
    except Exception as e:
        print("Erreur update_status :", e)


@bot.command()
async def joueurs(ctx):
    online, players, max_players = get_status()

    if online:
        await ctx.send(f"👥 {players}/{max_players} joueurs")
    else:
        await ctx.send("🔴 Serveur hors ligne")


bot.run(TOKEN)


