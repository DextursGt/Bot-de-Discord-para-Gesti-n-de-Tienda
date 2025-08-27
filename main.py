import discord
from discord import app_commands
import sys
import os

# Esto nos ayuda a encontrar nuestros archivos sin problemas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos todo lo que necesitamos para que el bot funcione
from config import DISCORD_TOKEN, intents
from commands.owner_commands import setup as setup_owner_commands
from commands.user_commands import setup as setup_user_commands
from commands.general_commands import setup as setup_general_commands
from commands.category_commands import setup as setup_category_commands
from commands.economy_commands import setup as setup_economy_commands
from commands.virtual_shop_commands import setup as setup_virtual_shop_commands

from utils import setup_error_handlers

from reminder_system import initialize_reminder_system

# Aquí creamos nuestro bot y le damos vida
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Esta función prepara todo lo que el bot necesita para funcionar correctamente
async def setup():
    # Cargamos todos los comandos disponibles para diferentes tipos de usuarios
    setup_owner_commands(tree, client)      # Comandos solo para administradores
    setup_user_commands(tree, client)       # Comandos que todos pueden usar
    setup_general_commands(tree, client)    # Comandos básicos y útiles
    setup_category_commands(tree, client)   # Para organizar productos
    setup_economy_commands(tree, client)    # Sistema de monedas y economía
    setup_virtual_shop_commands(tree, client) # Nuestra tienda virtual

    # Configuramos cómo manejar los errores de forma elegante
    await setup_error_handlers(tree)

# Todo esto se ejecutará cuando el bot arranque

@client.event
async def on_ready():
    print(f"Activo {client.user} ")
    
    # Le decimos a Discord qué está haciendo nuestro bot
    activity = discord.Activity(type=discord.ActivityType.playing, name="Gestionando Tickets y Productos")
    await client.change_presence(activity=activity)
    
    # Sincronizamos todos los comandos con Discord
    try:
        synced = await tree.sync()
        print(f"¡Perfecto! He cargado {len(synced)} comandos ")
    except Exception as e:
        print(f"Ocurrió un error al sincronizar los comandos: {e}")
    
    # Arrancamos el sistema que recuerda a los usuarios sobre sus Robux
    try:
        reminder_system = initialize_reminder_system(client)
        await reminder_system.start_reminder_system()
        print("Sistema de recordatorios funcionando perfectamente ")
    except Exception as e:
        print(f"No pude iniciar los recordatorios: {e}")



# Nos aseguramos de que tenemos el token para conectarnos a Discord
if not DISCORD_TOKEN:
    print("¡Oops! Parece que falta el token de Discord ")
    print("Por favor, asegúrate de configurar DISCORD_TOKEN en tu archivo de configuración")
    exit(1)

# Esta es la función principal que arranca todo
async def main():
    await setup()  
    await client.start(DISCORD_TOKEN)  

#
if __name__ == "__main__":
    import asyncio
    print("Iniciando BOT.")
    asyncio.run(main())