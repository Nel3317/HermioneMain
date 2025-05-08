# Hermione Main

# Imports -----------
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
from discord import app_commands, Interaction, Embed, Colour
from discord.utils import get
from discord.ext.commands import CommandOnCooldown
import aiomysql
import mysql.connector
import sqlite3
import aiohttp
import requests
import psutil
import logging
import json
import re
import io
import os
from dotenv import load_dotenv
import sys
import time
import asyncio
import random
import pytz
import unicodedata
from unidecode import unidecode
from googletrans import Translator
from typing import Union, Optional, Final
from collections import defaultdict
from contextlib import asynccontextmanager
from functools import wraps
from datetime import datetime, timezone, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pathlib
from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone
from datetime import datetime

# Importacion del token 

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Intents 
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.dm_messages = True
intents.voice_states = True 
intents.guild_messages = True 
gmt_minus_3 = timezone(timedelta(hours=-3)) 

# Conexión SQL 

async def get_db_connection():
    return await aiomysql.connect(
        host="db-buf-05.sparkedhost.us",           
        user="u145086_WEnjcROHKe",                
        password="pFbR=uL5!pXXX!@YfHtpATbO",   
        db="s145086_s145086_NEL_DB",  
        charset="utf8mb4"           
    )

async def get_db_connection():
    return await aiomysql.connect(
        host="db-buf-05.sparkedhost.us",
        user="u145086_WEnjcROHKe",
        password="pFbR=uL5!pXXX!@YfHtpATbO",
        db="s145086_s145086_NEL_DB",
        autocommit=True
    )

# Función para obtener el prefijo desde la base de datos MySQL
async def get_prefix(bot, message):
    guild_id = message.guild.id if message.guild else None
    if guild_id:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,))
            result = await cursor.fetchone()
            conn.close()
            if result:
                return commands.when_mentioned_or(result[0])(bot, message)
    
    # Si no existe el prefijo personalizado, usar un prefijo por defecto (y permitir mención)
    return commands.when_mentioned_or('t!')(bot, message)

# Crear la instancia del bot con 4 shards
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.AutoShardedBot(
    command_prefix=get_prefix,  # Prefijo dinámico
    shard_count=2,  # Establecer 2 shards
    intents=intents,  # Intents para gestionar eventos
    help_command=None  # Desactivar el comando de ayuda por defecto
)

# Comando para cambiar el prefijo del servidor
@bot.command(name="setprefix")
@commands.has_permissions(administrator=True)
async def set_prefix(ctx, new_prefix: str):
    if len(new_prefix) > 10:
        await ctx.send("The prefix cannot be longer than 10 characters.")
        return
    
    guild_id = ctx.guild.id
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Insertar o actualizar el prefijo en la base de datos MySQL
        await cursor.execute("INSERT INTO prefixes (guild_id, prefix) VALUES (%s, %s) ON DUPLICATE KEY UPDATE prefix = %s", 
                             (guild_id, new_prefix, new_prefix))
        await conn.commit()
    conn.close()
    
    await ctx.send(f"Prefix updated to: `{new_prefix}`")

# Comando para eliminar el prefijo personalizado y restaurar el prefijo por defecto
@bot.command(name="delprefix")
@commands.has_permissions(administrator=True)
async def del_prefix(ctx):
    guild_id = ctx.guild.id
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Eliminar el prefijo del servidor de la base de datos MySQL
        await cursor.execute("DELETE FROM prefixes WHERE guild_id = %s", (guild_id,))
        await conn.commit()
    conn.close()
    
    await ctx.send("Prefix has been reset to default (`$`).")

# Manejar errores de permisos
@set_prefix.error
@del_prefix.error
async def prefix_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need administrator permissions to change or delete the prefix.")


#----- Economía -----

# WORK

#Cooldonw de trabajo
cooldowns = {}
COOLDOWN_TIME = 120  

@bot.command(name='work', aliases=['trabajo', 'chamba'])
async def work(ctx):
    if await check_cooldown(ctx):
        await perform_work(ctx)
    else:
        await send_cooldown_message(ctx)

@bot.tree.command(name='work', description='Realiza un trabajo y gana galeones.')
async def work_slash(interaction: discord.Interaction):
    if await check_cooldown(interaction):
        await perform_work(interaction)
    else:
        await send_cooldown_message(interaction)

async def check_cooldown(ctx):
    now = datetime.now(tz=timezone.utc).timestamp()
    user_id = str(ctx.author.id) if isinstance(ctx, commands.Context) else str(ctx.user.id)
    guild_id = str(ctx.guild.id)
    cooldown_key = f"{guild_id}-{user_id}"

    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Verificar si el perfil ya existe
        await c.execute("SELECT 1 FROM profile WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        exists = await c.fetchone()

        # Si no existe, insertar con la fecha actual en formato Unix
        if not exists:
            timestamp = int(datetime.now(tz=timezone.utc).timestamp())
            await c.execute("INSERT INTO profile (guild_id, user_id, created_at) VALUES (%s, %s, %s)", 
                            (guild_id, user_id, timestamp))
            await conn.commit()

        # Aquí sigue la lógica normal del economy
        await c.execute("SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result:
            current_coins = result[0]
        else:
            current_coins = 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)",
                            (guild_id, user_id, 0, 0))
            await conn.commit() 

    # Verificar el cooldown
    if cooldown_key in cooldowns:
        last_used = cooldowns[cooldown_key]
        if now - last_used < COOLDOWN_TIME:
            return False  
    cooldowns[cooldown_key] = now
    return True

async def send_cooldown_message(ctx):
    now = datetime.now(tz=timezone.utc).timestamp()
    user_id = str(ctx.author.id) if isinstance(ctx, commands.Context) else str(ctx.user.id)
    guild_id = str(ctx.guild.id)
    cooldown_key = f"{guild_id}-{user_id}"

    if cooldown_key in cooldowns:
        last_used = cooldowns[cooldown_key]
        remaining_time = COOLDOWN_TIME - (now - last_used)
        minutes, seconds = divmod(int(remaining_time), 60)

        embed = discord.Embed(
            title="<:Hermyno:1291580187376619551> Comando en Enfriamiento",
            description=f"¡Aún no puedes trabajar! Inténtalo de nuevo en {minutes} minutos y {seconds} segundos.",
            color=0xFF0000,
            timestamp=datetime.now()
        )

        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

async def perform_work(ctx):
    if isinstance(ctx, discord.Interaction):
        await ctx.response.defer()

    guild = ctx.guild
    role_name = "🌆 • Ciudadano Mágico"
    role = discord.utils.get(guild.roles, name=role_name)
    
    if role is None:
        try:
            role = await guild.create_role(name=role_name)
        except discord.Forbidden:
            return
    
    user = ctx.user if isinstance(ctx, discord.Interaction) else ctx.author
    if role not in user.roles:
        try:
            await user.add_roles(role)
        except discord.Forbidden:
            return

    guild_id = str(ctx.guild.id)
    user_id = str(user.id)

    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Verificar si el perfil ya existe
        await c.execute("SELECT 1 FROM profile WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        exists = await c.fetchone()

        if not exists:
            timestamp = int(datetime.now(tz=timezone.utc).timestamp())
            await c.execute("INSERT INTO profile (guild_id, user_id, created_at, work_count) VALUES (%s, %s, %s, %s)", 
                            (guild_id, user_id, timestamp, 0))
            await conn.commit()

        # Aumentar el contador de trabajos realizados - ahora solo se ejecuta cuando el trabajo realmente se realiza
        await c.execute("UPDATE profile SET work_count = work_count + 1 WHERE guild_id = %s AND user_id = %s", 
                        (guild_id, user_id))
        await conn.commit()
        
        # Continuar con la lógica original de economy
        await c.execute("SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result:
            current_coins = result[0]
        else:
            current_coins = 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)",
                            (guild_id, user_id, 0, 0))
            await conn.commit()

    # Lista de posibles trabajos y sus descripciones
    work_descriptions = [
        # Trabajos en el Callejón Diagon
        "Te aventuraste en el Callejón Diagon y ganaste {earnings} <:Galeones:1276365877494677556> por tu destreza.",
        "Ayudaste a Florean Fortescue en su heladería, sirviendo helados mágicos y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Trabajaste como asistente temporal en Flourish y Blotts ordenando libros mágicos y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Limpiaste las jaulas en la Tienda de Animales Mágicos y recibiste {earnings} <:Galeones:1276365877494677556> por tu esfuerzo.",
        "Ayudaste a Ollivander a clasificar nuevas varitas y te pagó {earnings} <:Galeones:1276365877494677556> por tu trabajo.",
        
        # Trabajos en Hogwarts
        "Sustituiste a Hagrid cuidando criaturas mágicas por un día y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Ayudaste a la Profesora Sprout en los invernaderos y recibiste {earnings} <:Galeones:1276365877494677556> por tu ayuda con las mandrágoras.",
        "Organizaste los ingredientes en el armario del Profesor Snape y te pagó {earnings} <:Galeones:1276365877494677556> a regañadientes.",
        "Limpiaste el despacho de Dumbledore y encontraste {earnings} <:Galeones:1276365877494677556> entre los artefactos mágicos.",
        
        # Trabajos en Hogsmeade
        "Serviste cervezas de mantequilla en Las Tres Escobas y recibiste {earnings} <:Galeones:1276365877494677556> en propinas.",
        "Ayudaste a reponer los estantes en Honeydukes y te pagaron {earnings} <:Galeones:1276365877494677556> más algunos dulces.",
        "Entregaste paquetes para la oficina postal de Hogsmeade y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Decoraste La Casa de los Gritos para una fiesta especial y recibiste {earnings} <:Galeones:1276365877494677556>.",
        
        # Trabajos en el Ministerio
        "Clasificaste archivos en el Departamento de Misterios y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Ayudaste a Arthur Weasley con artefactos muggles y te pagó {earnings} <:Galeones:1276365877494677556>.",
        "Trabajaste como asistente temporal en la oficina de Aurores y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Registraste nuevas varitas en el Departamento de Regulación Mágica y recibiste {earnings} <:Galeones:1276365877494677556>.",
        
        # Trabajos inusuales
        "Limpiaste el fondo del Lago Negro y encontraste {earnings} <:Galeones:1276365877494677556> entre los tesoros perdidos.",
        "Domesticaste un Hipogrifo salvaje para un circo mágico y ganaste {earnings} <:Galeones:1276365877494677556>.",
        "Recogiste ingredientes raros en el Bosque Prohibido y los vendiste por {earnings} <:Galeones:1276365877494677556>.",
        "Ayudaste a Fred y George a probar nuevos productos de Sortilegios Weasley y ganaste {earnings} <:Galeones:1276365877494677556> arriesgando tu salud.",
        "Pintaste un retrato mágico para la galería del Ministerio y te pagaron {earnings} <:Galeones:1276365877494677556>.",
        
        # Trabajos divertidos
        "Derrotaste a un boggart particularmente molesto en la casa de una anciana bruja y te recompensó con {earnings} <:Galeones:1276365877494677556>.",
        "Ayudaste a Rita Skeeter a conseguir algunos chismes jugosos y te pagó {earnings} <:Galeones:1276365877494677556> por tu silencio.",
        "Jugaste como buscador suplente en un partido de Quidditch y ganaste {earnings} <:Galeones:1276365877494677556> por atrapar la snitch.",
        "Hiciste de modelo para una nueva línea de túnicas en Madame Malkin y recibiste {earnings} <:Galeones:1276365877494677556>.",
        "Desgnomizaste el jardín de los Weasley y Molly te pagó {earnings} <:Galeones:1276365877494677556> más una cena deliciosa."
    ]
    
    earnings = random.randint(1500, 3200)
    # Elegir una descripción aleatoria y formatearla con las ganancias
    description = random.choice(work_descriptions).format(earnings=earnings)
    new_coins = current_coins + earnings

    async with conn.cursor() as c:
        await c.execute("UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s", (new_coins, guild_id, user_id))
        await conn.commit()

    conn.close()

    avatar_url = user.avatar.url if user.avatar else "https://cdn.discordapp.com/avatars/default.png"
    
    # Lista de posibles URLs de imágenes temáticas para los trabajos
    work_thumbnails = [
        "https://www.hermionebot.xyz/imagework1.png",
        "https://www.hermionebot.xyz/imagework2.png",
        "https://www.hermionebot.xyz/imagework3.png",
        "https://www.hermionebot.xyz/imagework4.png"
    ]
    
    embed = discord.Embed(
        title="Trabajo Realizado", 
        description=description, 
        color=0x8A2BE2,
        timestamp=datetime.now()
    )
    embed.set_author(name=user.name, icon_url=avatar_url)
    embed.set_thumbnail(url=random.choice(work_thumbnails))
    embed.set_footer(text="¡Sigue trabajando para ganar más galeones!")

    if isinstance(ctx, discord.Interaction):
        await ctx.followup.send(embed=embed)
    else:
        await ctx.send(embed=embed)


# DEPOSITO

@bot.command(name='dep', aliases=['depositar', 'guardar'])
async def deposit(ctx, amount: str = None):
    await process_deposit(ctx, amount)

@bot.tree.command(name='deposit', description='Deposita tus Galeones en el banco de Gringotts.')
async def deposit(interaction: discord.Interaction, amount: str = None):
    await process_deposit(interaction, amount)

async def process_deposit(ctx_or_interaction, amount):
    conn = await get_db_connection()
    async with conn.cursor() as c:

        if isinstance(ctx_or_interaction, discord.Interaction):
            guild_id = str(ctx_or_interaction.guild.id)
            user_id = str(ctx_or_interaction.user.id)
        else:
            guild_id = str(ctx_or_interaction.guild.id)
            user_id = str(ctx_or_interaction.author.id)

        try:
            
            await c.execute("SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
            result = await c.fetchone()

            if result:
                coins, bank = result
            else:
                coins, bank = 0, 0
                await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)",
                                (guild_id, user_id, coins, bank))
                await conn.commit()

            
            if amount is None or amount.lower() == 'all':
                amount = coins
            else:
                try:
                    amount = int(amount)
                except ValueError:
                    await send_error_embed(ctx_or_interaction, "<:Hermyno:1291580187376619551>ㅤPor favor ingresa una cantidad válida.")
                    return

            
            if coins == 0:
                await send_error_embed(ctx_or_interaction, "<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**\n\n<:Hermyno:1291580187376619551>ㅤNo tienes Galeones en efectivo para depositar.")
            elif amount <= coins:
                
                new_coins = coins - amount
                new_bank = bank + amount
                await c.execute("UPDATE economy SET coins = %s, bank = %s WHERE guild_id = %s AND user_id = %s",
                                (new_coins, new_bank, guild_id, user_id))
                await conn.commit()
                await send_success_embed(ctx_or_interaction, f"<:Hermycheck:1290870881542737970>ㅤHas depositado {amount} <:Galeones:1276365877494677556> a tu banco.")
            else:
                await send_error_embed(ctx_or_interaction, "<:Hermyno:1291580187376619551>ㅤNo tienes suficientes Galeones en efectivo.")
        except aiomysql.Error as e:
            await send_error_embed(ctx_or_interaction, f"Ocurrió un error al acceder a la base de datos: {str(e)}")
        finally:
            conn.close()


async def send_success_embed(ctx_or_interaction, description):
    embed = discord.Embed(
        title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
        description=description,
        color=0x00FF00,
        timestamp=datetime.now()  
    )
    user = ctx_or_interaction.user if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.author
    embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)

    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(embed=embed)
    else:
        await ctx_or_interaction.send(embed=embed)


async def send_error_embed(ctx_or_interaction, message):
    embed = discord.Embed(
        description=message,
        color=0xFF0000,
        timestamp=datetime.now()  
    )
    user = ctx_or_interaction.user if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.author
    embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)

    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(embed=embed)
    else:
        await ctx_or_interaction.send(embed=embed)



# BALANCE

@bot.command(name='bal', aliases=['balance', 'cuenta', 'capital'])
async def bal(ctx, user: discord.User = None):
    conn = await get_db_connection()
    async with conn.cursor() as c:
        guild_id = str(ctx.guild.id)
        user_id = str(user.id) if user else str(ctx.author.id)

        
        await c.execute("SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result:
            coins, bank = result
        else:
            
            coins, bank = 0, 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", 
                            (guild_id, user_id, coins, bank))
            await conn.commit()


        try:
            total_coins = f"{int(coins):,}".replace(",", ".")
            total_bank = f"{int(bank):,}".replace(",", ".")
            total_amount = f"{int(coins + bank):,}".replace(",", ".")
        except ValueError:
            total_coins = "0"
            total_bank = "0"
            total_amount = "0"

        last_three_digits = user_id[-3:]
        user_name = user.name if user else ctx.author.name
        avatar_url = user.avatar.url if user and user.avatar else ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url

       
        await c.execute('''SELECT user_id, coins, bank FROM economy WHERE guild_id = %s''', (guild_id,))  
        rows = await c.fetchall()

        user_totals = {
            user_id: coins + bank for user_id, coins, bank in rows if (coins + bank) > 0
        }
        sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)[:100]
        user_rank = next((idx + 1 for idx, (uid, _) in enumerate(sorted_users) if uid == user_id), "No estás en el ranking")

        embed = discord.Embed(
            title="💼 • **Tu Resumen Financiero**",
            description="Aquí está un vistazo detallado de tu capital:",    
            color=0x8A2BE2
        )
        embed.set_author(name=user_name, icon_url=avatar_url)
        embed.add_field(
            name="💰 • **Total en Capital**", 
            value=f"`{total_amount}` <:Galeones:1276365877494677556>", 
            inline=False
        )
        embed.add_field(
            name=f"<:Gringotts_Bank:1276368414528503858> • Gringotts Bank | **Caja Fuerte N°{last_three_digits}**", 
            value=f"`{total_bank}` <:Galeones:1276365877494677556>", 
            inline=False
        )
        embed.add_field(
            name="**Cash Disponible**", 
            value=f"`{total_coins}` <:Galeones:1276365877494677556>", 
            inline=False
        )
        embed.set_footer(
            text=f"Leaderboard Rank: {user_rank} | {user_name}"
        )
        await ctx.send(embed=embed)
    
    conn.close()

@bot.tree.command(name="balance", description="Ver el balance financiero de un usuario o el tuyo")
@app_commands.describe(user="El usuario cuyo balance quieres ver (opcional)")
async def balance(interaction: discord.Interaction, user: discord.User = None):
    conn = await get_db_connection()
    async with conn.cursor() as c:
        guild_id = str(interaction.guild.id)
        user_id = str(user.id) if user else str(interaction.user.id)

        await c.execute("SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result:
            coins, bank = result
        else:
            coins, bank = 0, 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", 
                            (guild_id, user_id, coins, bank))
            await conn.commit()

        total_coins = f"{coins:,}".replace(",", ".")
        total_bank = f"{bank:,}".replace(",", ".")
        total_amount = f"{coins + bank:,}".replace(",", ".")

        last_three_digits = user_id[-3:]
        user_name = user.name if user else interaction.user.name
        avatar_url = user.avatar.url if user and user.avatar else interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url

        await c.execute('''SELECT user_id, coins, bank FROM economy WHERE guild_id = %s''', (guild_id,))
        rows = await c.fetchall()

        user_totals = {
            user_id: coins + bank for user_id, coins, bank in rows if (coins + bank) > 0
        }
        sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)[:100]
        user_rank = next((idx + 1 for idx, (uid, _) in enumerate(sorted_users) if uid == user_id), "No estás en el ranking")

        embed = discord.Embed(
            title="💼 • **Tu Resumen Financiero**",
            description="Aquí está un vistazo detallado de tu capital:",
            color=0x8A2BE2
        )
        embed.set_author(name=user_name, icon_url=avatar_url)
        embed.add_field(
            name="💰 • **Total en Capital**", 
            value=f"`{total_amount}` <:Galeones:1276365877494677556>", 
            inline=False
        )
        embed.add_field(
            name=f"<:Gringotts_Bank:1276368414528503858> •  Gringotts Bank | **Caja Fuerte N°{last_three_digits}**", 
            value=f"`{total_bank}` <:Galeones:1276365877494677556>", 
            inline=False
        )
        embed.add_field(
            name="**Cash Disponible**", 
            value=f"`{total_coins}` <:Galeones:1276365877494677556>", 
            inline=False
        )
        embed.set_footer(
            text=f"Leaderboard Rank: {user_rank} | {user_name}"
        )
        await interaction.response.send_message(embed=embed)
    conn.close()


# SACAR 

@bot.command(name='with', aliases=['withdraw', 'withd', 'sacar'])
async def withdraw1(ctx, amount: str):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    conn = await get_db_connection()
    async with conn.cursor() as c:
        await c.execute("SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result:
            coins, bank = result
        else:
            coins, bank = 0, 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", 
                            (guild_id, user_id, coins, bank))
            await conn.commit()

    if bank == 0:
        embed = discord.Embed(
            title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
            description="<:Hermyno:1291580187376619551>ㅤNo tienes ningún Galeón en el banco para retirar.",
            color=0xFF0000,
            timestamp=datetime.now()  
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)
        return

    if amount.lower() == 'all':
        amount = bank
    else:
        try:
            amount = int(amount)
        except ValueError:
            embed = discord.Embed(
                title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
                description="<:Hermyno:1291580187376619551>ㅤPor favor ingresa una cantidad válida.",
                color=0xFF0000,
                timestamp=datetime.now()  
            )
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            await ctx.send(embed=embed)
            return

    if amount <= bank:
        bank -= amount
        coins += amount
        
        async with conn.cursor() as c:
            await c.execute("UPDATE economy SET coins = %s, bank = %s WHERE guild_id = %s AND user_id = %s", 
                            (coins, bank, guild_id, user_id))
            await conn.commit()

        embed = discord.Embed(
            title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
            description=f"<:Hermycheck:1290870881542737970>ㅤHas retirado {amount} <:Galeones:1276365877494677556> del banco a tu efectivo.",
            color=0x00FF00,
            timestamp=datetime.now()  #
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
            description=f"<:Hermyno:1291580187376619551>ㅤNo tienes suficientes Galeones en el banco. Solo tienes {bank} <:Galeones:1276365877494677556>.",
            color=0xFF0000,
            timestamp=datetime.now()  
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    conn.close()


@bot.tree.command(name='withdraw', description='Retira dinero del banco.')
async def withdraw(interaction: discord.Interaction, amount: str = 'all'):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    conn = await get_db_connection()
    async with conn.cursor() as c:
        await c.execute("SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result:
            coins, bank = result
        else:
            coins, bank = 0, 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", 
                            (guild_id, user_id, coins, bank))
            await conn.commit()

    if bank == 0:
        embed = discord.Embed(
            title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
            description="<:Hermyno:1291580187376619551>ㅤNo tienes ningún Galeón en el banco para retirar.",
            color=0xFF0000,
            timestamp=datetime.now()  
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    if amount.lower() == 'all':
        amount = bank
    else:
        try:
            amount = int(amount)
        except ValueError:
            embed = discord.Embed(
                title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
                description="<:Hermyno:1291580187376619551>ㅤPor favor ingresa una cantidad válida.",
                color=0xFF0000,
                timestamp=datetime.now()  
            )
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
            await interaction.response.send_message(embed=embed)
            return

    if amount <= bank:
        bank -= amount
        coins += amount
        
        async with conn.cursor() as c:
            await c.execute("UPDATE economy SET coins = %s, bank = %s WHERE guild_id = %s AND user_id = %s", 
                            (coins, bank, guild_id, user_id))
            await conn.commit()

        embed = discord.Embed(
            title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
            description=f"<:Hermycheck:1290870881542737970>ㅤHas retirado {amount} <:Galeones:1276365877494677556> del banco a tu efectivo.",
            color=0x00FF00,
            timestamp=datetime.now()  
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="<:Gringotts_Bank:1276368414528503858> *Notificación de* **Gringotts Bank**",
            description=f"<:Hermyno:1291580187376619551>ㅤNo tienes suficientes Galeones en el banco. Solo tienes {bank} <:Galeones:1276365877494677556>.",
            color=0xFF0000,
            timestamp=datetime.now()  
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        await interaction.response.send_message(embed=embed)

    conn.close()


# Tabla de jugadores 

class LeaderboardView(discord.ui.View):
    def __init__(self, ctx, sorted_users, user_rank):
        super().__init__()
        self.ctx = ctx
        self.sorted_users = sorted_users
        self.page = 0
        self.per_page = 10  
        self.total_pages = (len(self.sorted_users) - 1) // self.per_page + 1
        self.user_rank = user_rank  
        self.update_buttons_state()  

    def format_leaderboard_page(self, page):
        start = page * self.per_page
        end = start + self.per_page
        page_users = self.sorted_users[start:end]
        lb_description = "\n".join(page_users)  
        return lb_description

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.update_buttons_state()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Siguiente", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
            self.update_buttons_state()
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    def update_buttons_state(self):
        """Actualiza el estado de los botones deshabilitándolos cuando no haya más páginas."""
        self.children[0].disabled = self.page == 0  
        self.children[1].disabled = self.page == self.total_pages - 1  

    def create_embed(self):
        embed = discord.Embed(
            title=f"<:Hermytop:1284186212206247957> {self.ctx.guild.name} Leaderboard",  
            description=f"Top usuarios por página",
            color=0x4B0082  
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1277162414877573242/1284183893502857318/coin01.webp?ex=66e5b4f3&is=66e46373&hm=02c92f0d9018776fcb7bdc87db6b557dc94c878578db366f539936dd360ee29a&")  # Imagen en el título

        lb_description = self.format_leaderboard_page(self.page)
        embed.add_field(
            name=f"Ranking - Página {self.page + 1}",
            value=lb_description or "No hay más usuarios en esta página.",
            inline=False
        )

        embed.set_footer(text=f"Página {self.page + 1} de {self.total_pages} | Your leaderboard rank: {self.user_rank}")
        return embed


async def get_member_safe(guild, user_id):
    member = guild.get_member(user_id)  
    if member is None:  
        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound:
            return None  # 
        except discord.HTTPException:
            return None  
    return member

async def show_leaderboard(ctx_or_interaction, is_slash=False):
    guild_id = str(ctx_or_interaction.guild.id)

    try:
        conn = await get_db_connection()
    except Exception as e:
        if is_slash:
            await ctx_or_interaction.response.send_message(f"Error conectando a la base de datos: {e}")
        else:
            await ctx_or_interaction.send(f"Error conectando a la base de datos: {e}")
        return

    async with conn.cursor() as c:
        try:
            
            await c.execute('''SELECT user_id, coins, bank FROM economy WHERE guild_id = %s''', (guild_id,))
            rows = await c.fetchall()

           
            print(rows)

            
            user_totals = {}

            
            for user_id, coins, bank in rows:
                
                coins = coins if coins is not None else 0
                bank = bank if bank is not None else 0
                total = coins + bank

    
                user_totals[str(user_id)] = total

            sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)

            if not sorted_users:
                message = "No hay usuarios con dinero en la economía de este servidor."
                if is_slash:
                    await ctx_or_interaction.response.send_message(message)
                else:
                    await ctx_or_interaction.send(message)
                return

            # Calcular el rango del usuario que ejecuta el comando
            user_id = str(ctx_or_interaction.user.id if is_slash else ctx_or_interaction.author.id)
            user_rank = next((idx + 1 for idx, (uid, _) in enumerate(sorted_users) if uid == user_id), "No estás en el ranking")

            # Preparar la lista de usuarios para el leaderboard
            sorted_users_with_names = []
            for idx, (uid, total) in enumerate(sorted_users):
                member = await get_member_safe(ctx_or_interaction.guild, int(uid))  
                if not member:
                    #
                    display_name = f"(Usuario ID: {uid} no está en el servidor)"
                else:
                    display_name = member.display_name

                
                if total >= 5_000_000_000:
                    formatted_total = "∞"
                else:
                    
                    formatted_total = f"{total:,}".replace(",", ".")

                
                sorted_users_with_names.append(f'**{idx + 1}.** `{display_name}`:  {formatted_total} <:Galeones:1276365877494677556>')

            
            leaderboard_view = LeaderboardView(ctx_or_interaction, sorted_users_with_names, user_rank)
            embed = leaderboard_view.create_embed()

            if is_slash:
                await ctx_or_interaction.response.send_message(embed=embed, view=leaderboard_view)
            else:
                await ctx_or_interaction.send(embed=embed, view=leaderboard_view)

        except Exception as e:
            if is_slash:
                await ctx_or_interaction.response.send_message(f"Error al obtener datos: {e}")
            else:
                await ctx_or_interaction.send(f"Error al obtener datos: {e}")

    conn.close()  


@bot.command(name='lb', aliases=['leaderboard', 'leaderb', 'top'])
async def lb(ctx):
    await show_leaderboard(ctx)


@bot.tree.command(name='leaderboard', description='Muestra el ranking de usuarios con más Galeones.')
async def lb(interaction: discord.Interaction):
    await show_leaderboard(interaction, is_slash=True)



# TRANSFERIR 

@bot.command(name='pass', aliases=['pasar', 'transferir']) 
async def pass_coins(ctx, user: discord.User, amount: str):
    sender_id = str(ctx.author.id)
    receiver_id = str(user.id)

    if amount.lower() == 'all':
        await transfer_coins(ctx, sender_id, receiver_id, amount=None, transfer_all=True)
    else:
        try:
            amount = int(amount)
            await transfer_coins(ctx, sender_id, receiver_id, amount)
        except ValueError:
            await ctx.send(embed=discord.Embed(description="El valor ingresado no es un número válido.", color=0xFF0000))

@bot.tree.command(name="pass", description="Transfiere coins a otro usuario.")
@app_commands.describe(user="El usuario que recibirá los coins", amount="Cantidad de coins o 'all' para transferir todo")
async def transferir(interaction: discord.Interaction, user: discord.User, amount: str):
    sender_id = str(interaction.user.id)
    receiver_id = str(user.id)

    if amount.lower() == 'all':
        await transfer_coins(interaction, sender_id, receiver_id, amount=None, is_interaction=True, transfer_all=True)
    else:
        try:
            amount = int(amount)
            await transfer_coins(interaction, sender_id, receiver_id, amount, is_interaction=True)
        except ValueError:
            await interaction.response.send_message(embed=discord.Embed(description="El valor ingresado no es un número válido.", color=0xFF0000), ephemeral=True)

async def transfer_coins(ctx_or_interaction, sender_id, receiver_id, amount, is_interaction=False, transfer_all=False):
    guild_id = str(ctx_or_interaction.guild.id)

    conn = await get_db_connection()
    async with conn.cursor() as c:
        
        if sender_id == receiver_id:
            error_message = "<:Gringotts_Bank:1276368414528503858>   *Notificación de* **Gringotts Bank** \n<:Hermyerror:1282524139135045642> No puedes transferirte a ti mismo."
            if is_interaction:
                await ctx_or_interaction.response.send_message(embed=discord.Embed(description=error_message, color=0xFF0000), ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=discord.Embed(description=error_message, color=0xFF0000))
            return

        await c.execute('SELECT bank FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, sender_id))
        sender_data = await c.fetchone()

        if sender_data is None or (not transfer_all and sender_data[0] < amount):
            error_message = "<:Gringotts_Bank:1276368414528503858>   *Notificación de* **Gringotts Bank** \n<:Hermyerror:1282524139135045642> No tienes suficientes Galeones <:Galeones:1276365877494677556> para transferir."
            if is_interaction:
                await ctx_or_interaction.response.send_message(embed=discord.Embed(description=error_message, color=0xFF0000), ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=discord.Embed(description=error_message, color=0xFF0000))
            return

        sender_bank = sender_data[0]

        if transfer_all:
            amount = sender_bank

        
        try:
            sender_member = await ctx_or_interaction.guild.fetch_member(int(sender_id))
            receiver_member = await ctx_or_interaction.guild.fetch_member(int(receiver_id))
        except discord.NotFound:
            error_message = "No se pudo encontrar al remitente o al receptor en el servidor."
            if is_interaction:
                await ctx_or_interaction.response.send_message(embed=discord.Embed(description=error_message, color=0xFF0000), ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=discord.Embed(description=error_message, color=0xFF0000))
            return
        except discord.HTTPException:
            error_message = "Ocurrió un error al intentar obtener los usuarios. Inténtalo de nuevo."
            if is_interaction:
                await ctx_or_interaction.response.send_message(embed=discord.Embed(description=error_message, color=0xFF0000), ephemeral=True)
            else:
                await ctx_or_interaction.send(embed=discord.Embed(description=error_message, color=0xFF0000))
            return

        
        await c.execute('SELECT bank FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, receiver_id))
        receiver_data = await c.fetchone()

        if receiver_data is None:
            await c.execute('INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)', (guild_id, receiver_id, 0, 0))
            await conn.commit()
            receiver_bank = 0
        else:
            receiver_bank = receiver_data[0]

        
        new_sender_bank = sender_bank - amount
        new_receiver_bank = receiver_bank + amount

        await c.execute('UPDATE economy SET bank = %s WHERE guild_id = %s AND user_id = %s', (new_sender_bank, guild_id, sender_id))
        await c.execute('UPDATE economy SET bank = %s WHERE guild_id = %s AND user_id = %s', (new_receiver_bank, guild_id, receiver_id))
        await conn.commit()

       
        sender_name = sender_member.nick if sender_member.nick else sender_member.name
        receiver_name = receiver_member.nick if receiver_member.nick else receiver_member.name

        
        success_message = f"<:Gringotts_Bank:1276368414528503858>   *Notificación de* **Gringotts Bank** \n<:Hermycheck:1290870881542737970> {sender_name} ha transferido {amount} <:Galeones:1276365877494677556> a {receiver_name}."
        embed = discord.Embed(description=success_message, color=0x00ff00)

        
        sender_avatar_url = sender_member.avatar.url if sender_member.avatar else 'https://cdn.discordapp.com/embed/avatars/1.png'
        embed.set_author(name=sender_name, icon_url=sender_avatar_url)

        if is_interaction:
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

    conn.close()


# VARITA 

@bot.hybrid_command(name='varita', with_app_command=True, description="Compra una varita en la tienda")
async def varita(ctx: commands.Context):
    conn = await get_db_connection()  
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    async with conn.cursor() as c:
        
        await c.execute("SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        row = await c.fetchone()

        if row:
            user_coins = row[0]
        else:
            
            user_coins = 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", 
                            (guild_id, user_id, 0, 0))
            await conn.commit()

        
        await c.execute("SELECT * FROM wands WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        wand = await c.fetchone()

        if wand:
            await send_embed(
                ctx,
                "<:if19harrypottercolourharryswand2:1276229225942225009>  Ya posees una varita!",
                f"{ctx.author.mention}, ya tienes una varita. Puedes repararla si está rota por 20,000 <:Galeones:1276365877494677556>."
            )
            return

        
        precio_varita = 100000

        
        if user_coins < precio_varita:
            await send_embed(
                ctx,
                "Galeones insuficientes",
                f"{ctx.author.mention}, necesitas 100,000 <:Galeones:1276365877494677556> en efectivo para poder adquirir una varita en Ollivanders <:if25harrypottercolourelderwand27:1277529036955979796>."
            )
            return

        
        embed_description = (
            "<:cc9b092daf393c8172b158593bb88326:1277530324569686036>  ¿Deseas comprar una varita por 100,000 <:Galeones:1276365877494677556>?\n\n"
            "Si tu varita se rompe, puedes repararla por 20,000 <:Galeones:1276365877494677556>."
        )
        initial_message = await send_embed(
            ctx,
            "Comprar una Varita",
            embed_description,
            color=0x8B4513
        )

        view = Confirm(ctx, {'coins': user_coins}, guild_id, precio_varita, conn)
        await initial_message.edit(view=view)  

async def send_embed(ctx, title, description, color=0x8B4513, image_url=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if image_url:  
        embed.set_image(url=image_url)
    return await ctx.send(embed=embed)

class Confirm(discord.ui.View):
    def __init__(self, ctx, user_data, guild_id, precio_varita, conn):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.user_data = user_data
        self.guild_id = guild_id
        self.precio_varita = precio_varita
        self.conn = conn

    @discord.ui.button(label="Sí", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("No puedes interactuar con este botón.", ephemeral=True)

        
        await interaction.response.defer()

        async with self.conn.cursor() as c:
            
            await c.execute("UPDATE economy SET coins = coins - %s WHERE guild_id = %s AND user_id = %s", 
                            (self.precio_varita, self.guild_id, str(self.ctx.author.id)))
            await self.conn.commit()

            
            wand_name = random.choice(["Roble", "Sauce", "Nogal", "Tejo", "Cerezo", "Abeto plateado", "Haya", "Abedul", "Castaño", "Cedro", "Ciprés", 
                            "Fresno", "Haya roja", "Pino negro", "Hickory", "Acacia", "Olmo", 
                            "Sauce llorón", "Espino", "Vid", "Haya dorada", "Serbal", "Nogal negro", 
                            "Manzano", "Álamo"])
            wand_core = random.choice(["pluma de fénix", "pelo de unicornio", "escama de dragón", "fibra de corazón de dragón", "nervio de trol", "hueso de basilisco", 
                            "escama de acromántula", "pelo de veela", "pluma de thestral", 
                            "pelo de kelpie", "fibra de bowtruckle", "savia de mandrágora", 
                            "pluma de águila arpía", "diente de dragón", "lágrima de fénix", 
                            "crin de thestral", "escama de sirena", "pelo de mantícora", 
                            "colmillo de cerbero", "veneno de acromántula", "cuerno de unicornio", 
                            "polvo de estrella fugaz", "pelo de leprechaun"])
            wand_length = random.choice(["12 pulgadas", "10 pulgadas", "11 pulgadas", "9 pulgadas", "13 pulgadas", "14 pulgadas", "9 ¾ pulgadas", "11 ½ pulgadas", 
                            "10 ¼ pulgadas", "13 ½ pulgadas", "15 pulgadas", "8 pulgadas", "16 pulgadas", 
                            "12 ¼ pulgadas", "9 ¼ pulgadas", "10 ¾ pulgadas", "13 ¼ pulgadas", 
                            "11 ¾ pulgadas", "12 ½ pulgadas", "9 ½ pulgadas", "14 ½ pulgadas", 
                            "15 ¼ pulgadas", "13 pulgadas", "11 pulgadas", "16 ½ pulgadas"])
            wand_flexibility = random.choice(["muy flexible", "flexible", "rígida", "moderadamente flexible", "bastante rígida", "ligeramente flexible", "muy inflexible", 
                                "extremadamente elástica", "suave", "frágil", "increíblemente rígida", 
                                "adaptable", "robusta", "delicada", "resistente", "flexible como un sauce", 
                                "ligeramente rígida", "moderadamente flexible", "extraordinariamente ágil", 
                                "firmemente elástica", "bastante flexible", "quebradiza", "duramente inflexible", 
                                "ágil y rápida", "quebradiza"])

            
            await c.execute("INSERT INTO wands (guild_id, user_id, wood, core, length, flexibility, durability) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (self.guild_id, str(self.ctx.author.id), wand_name, wand_core, wand_length, wand_flexibility, 10))  # Durabilidad inicial
            await self.conn.commit()

            
            wand_embed = discord.Embed(
                title="¡Varita Comprada!",
                description=f" Has adquirido una magnífica varita de **{wand_name}**. "
                 f"Con su núcleo de **{wand_core}**, esta varita tiene una longitud de **{wand_length}** y una flexibilidad de **{wand_flexibility}**.\n\n"
                 "¡Siente la magia fluir a través de ti mientras la sostienes! Tu nueva varita está lista para realizar hechizos increíbles y forjar tu destino.\n"
                            f""
                            "",
                color=0x8B4513
            )
            wand_embed.set_image(url="https://c.tenor.com/DlHkXeR_WAoAAAAC/tenor.gif")  
            await interaction.followup.send(embed=wand_embed)

        self.stop()  

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("No puedes interactuar con este botón.", ephemeral=True)

        await interaction.response.defer()

        
        await interaction.followup.send("Compra cancelada. ¡Gracias por visitar Ollivanders!")
        self.stop()  


# VER VARITA 
@bot.command(name='mivarita', aliases=['miv'])
async def mivarita_command(ctx):
    user_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id)

    conn = await get_db_connection()
    if conn is None:
        await ctx.send("Error al conectar a la base de datos.")
        return

    try:
        async with conn.cursor() as c:
            await c.execute('SELECT * FROM wands WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
            wand = await c.fetchone()

        if wand is None:
            embed = Embed(
                title="Sin varita",
                description=f"{ctx.author.mention}, no tienes una varita.",
                color=0xff0000  
            )
            embed.set_author(name=ctx.author.name.lower(), icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            return

       
        wood = wand[2]
        core = wand[3]
        length = wand[4]
        flexibility = wand[5]
        durability = wand[6]

        wand_info = (
            f"**Descripción de tu Varita:**\n\n"
            f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Madera:* {wood}\n"
            f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Núcleo:* {core}\n"
            f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Longitud:* {length}\n"
            f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Flexibilidad:* {flexibility}\n\n"
            f"**Durabilidad:** {durability}/10"
        )

        embed = Embed(
            title="<:cc9b092daf393c8172b158593bb88326:1277530324569686036>  Información de tu Varita",
            description=wand_info,
            color=0x8A2BE2  # Verde
        )
        embed.set_author(name=ctx.author.name.lower(), icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)
    
    finally:
       
        if conn is not None:
         conn.close()

@bot.tree.command(name='mivarita', description='Muestra la información de tu varita')
async def mivarita(interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)

    conn = await get_db_connection()
    if conn is None:
        await interaction.response.send_message("Error al conectar a la base de datos.")
        return

    async with conn.cursor() as c:
        await c.execute('SELECT * FROM wands WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        wand = await c.fetchone()

    if wand is None:
        embed = Embed(
            title="Sin varita",
            description=f"{interaction.user.mention}, no tienes una varita.",
            color=0xff0000  # Rojo
        )
        embed.set_author(name=interaction.user.name.lower(), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        await conn.close()
        return


    wood = wand[2]
    core = wand[3]
    length = wand[4]
    flexibility = wand[5]
    durability = wand[6]

    wand_info = (
        f"**Descripción de tu Varita:**\n\n"
        f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Madera:* {wood}\n"
        f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Núcleo:* {core}\n"
        f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Longitud:* {length}\n"
        f"<:if19harrypottercolourharryswand2:1276229225942225009>     • *Flexibilidad:* {flexibility}\n\n"
        f"**Durabilidad:** {durability}/10"
    )

    embed = Embed(
        title="<:cc9b092daf393c8172b158593bb88326:1277530324569686036>  Información de tu Varita",
        description=wand_info,
        color=0x8A2BE2  # Verde
    )
    embed.set_author(name=interaction.user.name.lower(), icon_url=interaction.user.avatar.url)

    await interaction.response.send_message(embed=embed)
    await conn.close()

# REPARAR VARITA


@bot.tree.command(name='reparar-varita', description="Repara tu varita por 20,000 galeones.")
async def reparar_varita(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)

    conn = await get_db_connection()
    
    
    precio_reparacion = 20000
    user_coins = await get_user_coins(guild_id, user_id, conn)

 
    if user_coins is None or user_coins[0] < precio_reparacion:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="<:cc9b092daf393c8172b158593bb88326:1277530324569686036> Monedas insuficientes",
                description=f"{interaction.user.mention}, no tienes suficientes Galeones para reparar tu varita. Necesitas 20,000 <:Galeones:1276365877494677556>.",
                color=0xFF4500  # Rojo 
            )
        )
        return

    
    wand_data = await get_wand_durability(guild_id, user_id, conn)
    if wand_data is None:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="No tienes una varita",
                description=f"{interaction.user.mention}, necesitas una varita para poder repararla. Usa /varita para obtener una en *Ollivanders*.",
                color=0xFF4500  # Rojo 
            )
        )
        return

 
    durability = wand_data[0]
    if durability > 0:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Tu varita está en buen estado",
                description=f"{interaction.user.mention}, tu varita no necesita reparaciones. Está en perfecto estado para seguir con tus aventuras mágicas.",
                color=0x8B4513  # Color marrón oscuro
            )
        )
        return

  
    await subtract_coins(guild_id, user_id, precio_reparacion, conn)

    
    await repair_wand(guild_id, user_id, conn)

    
    await interaction.response.send_message(
        embed=discord.Embed(
            title="<:cc9b092daf393c8172b158593bb88326:1277530324569686036> Varita reparada",
            description=f"{interaction.user.mention}, Ollivanders ha reparado tu varita con gran cuidado. Tu varita ha sido restaurada a su estado óptimo, lista para ser usada en nuevas aventuras mágicas.",
            color=0x8B4513  # Color marrón oscuro
        ).set_image(url="https://media1.tenor.com/m/IuxEgYiKTTkAAAAC/hogwarts-legacy-warner-bros-interactive-entertainment.gif")  # GIF de Ollivanders
    )
    
    conn.close()


async def get_user_coins(guild_id, user_id, conn):
    async with conn.cursor() as c:
        await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        return await c.fetchone()


async def get_wand_durability(guild_id, user_id, conn):
    async with conn.cursor() as c:
        await c.execute('SELECT durability FROM wands WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        return await c.fetchone()


async def subtract_coins(guild_id, user_id, amount, conn):
    async with conn.cursor() as c:
        await c.execute('UPDATE economy SET coins = coins - %s WHERE guild_id = %s AND user_id = %s', (amount, guild_id, user_id))
        await conn.commit()


async def repair_wand(guild_id, user_id, conn):
    async with conn.cursor() as c:
        await c.execute('UPDATE wands SET durability = 10 WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        await conn.commit()


@bot.command(name='repvarita', aliases=['repv', 'repararvarita'])
async def reparar_varita(ctx):
    user_id = str(ctx.author.id)
    guild_id = str(ctx.guild.id)

    conn = await get_db_connection()
    

    precio_reparacion = 20000
    user_coins = await get_user_coins(guild_id, user_id, conn)

   
    if user_coins is None or user_coins[0] < precio_reparacion:
        await ctx.send(
            embed=discord.Embed(
                title="Monedas insuficientes",
                description=f"{ctx.author.mention}, no tienes suficientes Galeones para reparar tu varita. Necesitas 20,000 Galeones.",
                color=0xFF4500  # Rojo 
            )
        )
        return

    wand_data = await get_wand_durability(guild_id, user_id, conn)
    if wand_data is None:
        await ctx.send(
            embed=discord.Embed(
                title="No tienes una varita",
                description=f"{ctx.author.mention}, necesitas una varita para poder repararla. Usa /varita para obtener una en Ollivanders.",
                color=0xFF4500  # Rojo 
            )
        )
        return

  
    durability = wand_data[0]
    if durability > 0:
        await ctx.send(
            embed=discord.Embed(
                title="Tu varita está en buen estado",
                description=f"{ctx.author.mention}, tu varita no necesita reparaciones. Está en perfecto estado para seguir con tus aventuras mágicas.",
                color=0x8B4513  # Color marrón oscuro
            )
        )
        return


    await subtract_coins(guild_id, user_id, precio_reparacion, conn)


    await repair_wand(guild_id, user_id, conn)

    await ctx.send(
        embed=discord.Embed(
            title="Varita reparada",
            description=f"{ctx.author.mention}, Ollivanders ha reparado tu varita con gran cuidado. Tu varita ha sido restaurada a su estado óptimo, lista para ser usada en nuevas aventuras mágicas.",
            color=0x8B4513  # Color marrón oscuro
        ).set_image(url="https://media1.tenor.com/m/IuxEgYiKTTkAAAAC/hogwarts-legacy-warner-bros-interactive-entertainment.gif")  # GIF de Ollivanders
    )
    
    conn.close()

# SEGURIDAD 

COOLDOWN_TIMESEG = 0 
user_cooldowns = {}


@bot.command(name='seguridad', aliases=['seg', 'security'])
async def seguridad_prefijo(ctx: commands.Context):
    await realizar_trabajo(ctx, ctx.author, ctx.guild)


@bot.tree.command(name='seguridad', description="Realiza un trabajo de seguridad mágica como Auror.")
async def seguridad_slash(interaction: discord.Interaction):
    await realizar_trabajo(interaction, interaction.user, interaction.guild)

async def realizar_trabajo(source, author, guild):
    user_id = str(author.id)
    guild_id = str(guild.id)
    current_time = discord.utils.utcnow().timestamp()

    
    if guild_id not in user_cooldowns:
        user_cooldowns[guild_id] = {}

    last_used = user_cooldowns[guild_id].get(user_id, 0)
    if current_time - last_used < COOLDOWN_TIMESEG:
        time_left = COOLDOWN_TIMESEG - (current_time - last_used)
        minutes, seconds = divmod(int(time_left), 60)

        # Crear embed para el enfriamiento
        embed = discord.Embed(
            title="<:Hermyno:1291580187376619551> Comando en enfriamiento",
            description=f"¡Aún no puedes hacer trabajos de seguridad! Inténtalo de nuevo en {minutes} minutos y {seconds} segundos.",
            color=0xFF0000  # Rojo para error
        )
        await enviar_mensaje(source, embed)
        return

    conn = await get_db_connection()
    async with conn.cursor() as c:
        
        await c.execute('SELECT durability FROM wands WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        wand = await c.fetchone()

        if wand is None:
            embed = discord.Embed(
                title="No tienes una varita",
                description=f"{author.mention}, necesitas una varita para realizar este trabajo. Usa /varita para obtener una en *Ollivanders*.",
                color=0xFF0000  
            )
            await enviar_mensaje(source, embed)
            return

        wand_durability = wand[0]

        
        if wand_durability == 0:
            embed = discord.Embed(
                title="Varita Rota",
                description=f"{author.mention}, tu varita está rota y no puedes realizar este trabajo. Ve a *Ollivanders* para repararla.",
                color=0xFF0000  
            )
            await enviar_mensaje(source, embed)
            return

        
        coins_earned = random.randint(1000, 6000)

       
        await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        user_data = await c.fetchone()

        if user_data is None:
            await c.execute('INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)', (guild_id, user_id, coins_earned, 0))
        else:
            new_coins = user_data[0] + coins_earned
            await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (new_coins, guild_id, user_id))

        
        await conn.commit()

        
        if wand_durability > 0:
            new_durability = wand_durability - 1
            await c.execute('UPDATE wands SET durability = %s WHERE guild_id = %s AND user_id = %s', (new_durability, guild_id, user_id))

            
            await conn.commit()

        
        descriptions = [  
            f"Con un destello de tu varita, neutralizaste a un mago oscuro que intentaba escapar con un artefacto prohibido. Has recibido {coins_earned} <:Galeones:1276365877494677556> como recompensa por tu valentía.",
            
        ]

        chosen_description = random.choice(descriptions)

        
        embed = discord.Embed(
            title="Trabajo de Seguridad Mágica",
            description=chosen_description,
            color=0x8A2BE2,
            timestamp=datetime.now()  
        )
        avatar_url = author.avatar.url if author.avatar else "https://cdn.discordapp.com/attachments/1252053297393700885/1280946642517753876/Sin_avatar_1.png"
        embed.set_author(name=author.name, icon_url=avatar_url)  
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1287495846262341729/1288238085292818472/OIG3.png")  

        await enviar_mensaje(source, embed)

       
        user_cooldowns[guild_id][user_id] = current_time

    conn.close()  


async def enviar_mensaje(source, embed):
    if isinstance(source, commands.Context):
        await source.send(embed=embed)
    elif isinstance(source, discord.Interaction):
        await source.response.send_message(embed=embed)


def close_db(conn):
    conn.commit()
    conn.close()


async def get_user_coins(guild_id, user_id, conn):
    async with conn.cursor() as c:
        await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        return await c.fetchone()


async def get_wand_durability(guild_id, user_id, conn):
    async with conn.cursor() as c:
        await c.execute('SELECT durability FROM wands WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        return await c.fetchone()


async def subtract_coins(guild_id, user_id, amount, conn):
    async with conn.cursor() as c:
        await c.execute('UPDATE economy SET coins = coins - %s WHERE guild_id = %s AND user_id = %s', (amount, guild_id, user_id))
        await conn.commit()


async def repair_wand(guild_id, user_id, conn):
    async with conn.cursor() as c:
        await c.execute('UPDATE wands SET durability = 10 WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        await conn.commit()

# Definir las opciones del destino 
class CoinDestination:
    BANK = "bank"
    CASH = "cash"

@bot.tree.command(name="add-galleons", description="Añade monedas a un usuario específico.")
@app_commands.describe(user="El usuario al que se le otorgarán las monedas", amount="La cantidad de monedas a agregar", destination="Destino para las monedas (bank o cash)")
@app_commands.choices(destination=[
    app_commands.Choice(name="Bank", value=CoinDestination.BANK),
    app_commands.Choice(name="Cash", value=CoinDestination.CASH),
])
async def give_coins(interaction: discord.Interaction, user: discord.User, amount: int, destination: app_commands.Choice[str]):
    # Verificar si el usuario tiene permisos de administrador
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(title="<:Hermyerror:1282524139135045642>", 
                              description="Solo los administradores pueden usar este comando.",
                              color=0xff0000)  # Rojo para el error
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    user_id = str(user.id)

    conn = await get_db_connection()  # Conectar a la base de datos
    async with conn.cursor() as c:
        # Verificar si el usuario ya está en la base de datos
        await c.execute('SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        result = await c.fetchone()

        if result is None:
            # Si no existe el usuario en la base de datos, lo inserta con monedas 0
            await c.execute('INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)', 
                            (guild_id, user_id, 0, 0))
            await conn.commit()
            user_coins, user_bank = 0, 0
        else:
            user_coins, user_bank = result

        embed = discord.Embed(color=0x00ff00)  # Color verde para el embed

        # Convertir el destino a string para la comparación
        destination_str = destination.value

        if destination_str == CoinDestination.BANK:
            # Agregar al banco
            new_bank = user_bank + amount
            total_amount = user_coins + new_bank  # Sumar monedas y banco

            if total_amount > 5000000000:
                embed.title = "<:Hermyerror:1282524139135045642> Error"
                embed.description = f"No puedes añadir más monedas a {user.mention} ya que superaría el límite máximo de 5,000,000,000 Galeones."
            else:
                await c.execute('UPDATE economy SET bank = %s WHERE guild_id = %s AND user_id = %s', 
                                (new_bank, guild_id, user_id))
                await conn.commit()
                embed.title = "<:Hermyaplicados:1282886092348981319> Coins Otorgados al Banco"
                embed.description = f"Has añadido {amount} <:Galeones:1276365877494677556> al banco de {user.mention}."
        elif destination_str == CoinDestination.CASH:
            # Agregar al efectivo
            new_coins = user_coins + amount
            total_amount = new_coins + user_bank  # Sumar monedas y banco

            if total_amount > 5000000000:
                embed.title = "<:Hermyerror:1282524139135045642> Error"
                embed.description = f"No puedes dar tantos Galeones a {user.mention} ya que superaría el límite máximo de 5,000,000,000 Galeones."
            else:
                await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', 
                                (new_coins, guild_id, user_id))
                await conn.commit()
                embed.title = "<:Hermyaplicados:1282886092348981319> Coins Otorgados"
                embed.description = f"Has dado {amount} <:Galeones:1276365877494677556> a {user.mention}."

    await interaction.response.send_message(embed=embed)
    conn.close()  # Cerrar la conexión a la base de datos

# Comando para agregar ítems 
@bot.tree.command(name='add-item', description='Añade un ítem a la tienda.')
@app_commands.describe(
    item_name="Nombre del ítem",
    price="Precio del ítem",
    description="Descripción del ítem",
    role="Rol asignado (opcional)",
    collect_amount="Cantidad a recolectar",
    collect_interval="Intervalo de recolección en segundos"
)
async def add_item1(
    interaction: discord.Interaction,
    item_name: str, 
    price: int, 
    description: str, 
    collect_amount: int, 
    collect_interval: int, 
    role: discord.Role = None
):
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permiso para usar este comando.", ephemeral=True)
        return

    
    if len(item_name) > 50:
        await interaction.response.send_message("El nombre del ítem no puede exceder los 50 caracteres.", ephemeral=True)
        return
    if len(description) > 150:
        await interaction.response.send_message("La descripción no puede exceder los 150 caracteres.", ephemeral=True)
        return
    if collect_amount > 5000000000 or collect_amount < 0:
        await interaction.response.send_message("La cantidad a recolectar debe estar entre 0 y 5,000,000,000.", ephemeral=True)
        return
    if collect_interval > 5000000000 or collect_interval < 0:
        await interaction.response.send_message("El intervalo de recolección debe estar entre 0 y 5,000,000,000.", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    item = {
        'price': price,
        'description': description,
        'role_id': role.id if role else None,
        'collect_amount': collect_amount,
        'collect_interval': collect_interval,
    }

 
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute('''
            INSERT INTO shop (guild_id, item_name, price, description, role_id, collect_amount, collect_interval)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price=%s, description=%s, role_id=%s, collect_amount=%s, collect_interval=%s
        ''', (
            guild_id, item_name.lower(), price, description, item['role_id'], item['collect_amount'], item['collect_interval'],
            price, description, item['role_id'], item['collect_amount'], item['collect_interval']
        ))
        await conn.commit()

    conn.close()

   
    embed = discord.Embed(title="¡Ítem añadido a la tienda!", color=0x00ff00)
    embed.add_field(name="Ítem", value=f"`{item_name}` añadido por `{price:,}` <:Galeones:1276365877494677556>.\nDescripción: {description}")
    if role:
        embed.add_field(name="Rol Asignado", value=f"Este ítem otorga el rol `{role.name}`.", inline=False)
    embed.add_field(name="Recolección", value=f"Este ítem permite recolectar `{collect_amount:,}` <:Galeones:1276365877494677556> cada `{collect_interval}` segundos.", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='update-item', description='Actualiza un ítem en la tienda.')
@app_commands.describe(
    item_name="Nombre del ítem",
    price="Nuevo precio del ítem (opcional)",
    description="Nueva descripción del ítem (opcional)",
    role="Nuevo rol asignado (opcional)",
    collect_amount="Nueva cantidad a recolectar (opcional)",
    collect_interval="Nuevo intervalo de recolección en segundos (opcional)"
)
async def update_item(
    interaction: discord.Interaction,
    item_name: str,
    price: int = None,
    description: str = None,
    role: discord.Role = None,
    collect_amount: int = None,
    collect_interval: int = None
):
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            description="No tienes permiso para usar este comando.", color=0x8A2BE2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute('SELECT * FROM shop WHERE guild_id = %s AND item_name = %s', (guild_id, item_name.lower()))
        item = await cursor.fetchone()

        if not item:
            embed = discord.Embed(
                title="Error", description=f"⚠️ El ítem `{item_name}` no existe en la tienda.", color=0x8A2BE2
            )
            await interaction.response.send_message(embed=embed)
            await conn.ensure_closed()
            return

        if description and len(description) > 150:
            await interaction.response.send_message("La nueva descripción no puede exceder los 150 caracteres.", ephemeral=True)
            await conn.ensure_closed()
            return

        if collect_amount is not None and not (0 <= collect_amount <= 5000000000):
            await interaction.response.send_message("La cantidad a recolectar debe estar entre 0 y 5,000,000,000.", ephemeral=True)
            await conn.ensure_closed()
            return
        
        if collect_interval is not None and not (0 <= collect_interval <= 5000000000):
            await interaction.response.send_message("El intervalo de recolección debe estar entre 0 y 5,000,000,000.", ephemeral=True)
            await conn.ensure_closed()
            return

        update_fields = []
        update_values = []

        if price is not None:
            update_fields.append('price = %s')
            update_values.append(price)
        if description is not None:
            update_fields.append('description = %s')
            update_values.append(description)
        if role is not None:
            update_fields.append('role_id = %s')
            update_values.append(role.id)
        if collect_amount is not None:
            update_fields.append('collect_amount = %s')
            update_values.append(collect_amount)
        if collect_interval is not None:
            update_fields.append('collect_interval = %s')
            update_values.append(collect_interval)

        if update_fields:
            update_values.append(guild_id)
            update_values.append(item_name.lower())
            query = f"UPDATE shop SET {', '.join(update_fields)} WHERE guild_id = %s AND item_name = %s"
            await cursor.execute(query, update_values)
            embed = discord.Embed(
                title="Actualización exitosa",
                description=f"🔄 Ítem `{item_name}` actualizado en la tienda.",
                color=0x8A2BE2
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="Error", description="⚠️ No se han proporcionado campos para actualizar.", color=0x8A2BE2
            )
            await interaction.response.send_message(embed=embed)

    await conn.ensure_closed()

@bot.tree.command(name='remove-item', description='Elimina un ítem de la tienda.')
@app_commands.describe(item_name="Nombre del ítem a eliminar")
async def remove_item(interaction: discord.Interaction, item_name: str):
    # Verificar si el usuario tiene permisos de administrador
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="",
            description="No tienes permiso para usar este comando.",
            color=0x8A2BE2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild_id = str(interaction.guild.id)

    # Obtener la conexión a la base de datos
    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Verificar si el ítem existe en la tienda del servidor actual
        await c.execute('SELECT item_name FROM shop WHERE guild_id = %s AND item_name = %s', (guild_id, item_name.lower()))
        item = await c.fetchone()

        if not item:
            embed = discord.Embed(
                title="",
                description=f"⚠️ El ítem `{item_name}` no existe en la tienda de este servidor.",
                color=0x8A2BE2
            )
            await interaction.response.send_message(embed=embed)
            await conn.ensure_closed()
            return

        # Marcar el ítem como no disponible (is_available = 0)
        await c.execute('UPDATE shop SET is_available = 0 WHERE guild_id = %s AND item_name = %s', (guild_id, item_name.lower()))
        await conn.commit()

    embed = discord.Embed(
        title="Eliminación exitosa",
        description=f"<:Hermycheck:1290870881542737970> El ítem `{item_name}` ha sido marcado como no disponible en la tienda.",
        color=0x8A2BE2
    )
    await interaction.response.send_message(embed=embed)

    # Cerrar la conexión a la base de datos
    await conn.ensure_closed()


# Collect

class CollectView(discord.ui.View):
    def __init__(self, user_id, guild_id, user_items, user):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.guild_id = guild_id
        self.user_items = user_items
        self.user = user

    @discord.ui.button(label="Tiempo para próximo collect", style=discord.ButtonStyle.blurple)
    async def show_time_remaining(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_time = time.time()
        embed = discord.Embed(title="\u23f3 Tiempo restante para los ítems", color=0x8A2BE2)
        embed.set_author(
            name=f"{self.user.name}",
            icon_url=self.user.avatar.url if self.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        )

        conn = await get_db_connection()
        async with conn.cursor() as c:
            user_roles = {str(role.id) for role in interaction.user.roles}

            for row in self.user_items:
                item_name, last_collect = row[:2]

                await c.execute(
                    'SELECT role_id FROM shop WHERE guild_id = %s AND item_name = %s',
                    (self.guild_id, item_name)
                )
                role_required = await c.fetchone()

                if not role_required or role_required[0] not in user_roles:
                    continue

                await c.execute(
                    'SELECT last_collect, collect_interval FROM collect_data WHERE guild_id = %s AND user_id = %s AND item_name = %s',
                    (self.guild_id, self.user_id, item_name)
                )
                item_data = await c.fetchone()
                if not item_data:
                    continue

                last_collect, collect_interval = item_data
                last_collect = last_collect if last_collect is not None else 0
                collect_interval = collect_interval if collect_interval is not None else 0

                time_until_next_collect = collect_interval - (current_time - last_collect) + 5
                time_until_next_collect = max(0, time_until_next_collect)

                if time_until_next_collect > 0:
                    embed.add_field(name=item_name, value=f"Disponible <t:{int(current_time + time_until_next_collect)}:R>", inline=False)
                else:
                    embed.add_field(name=item_name, value="¡Disponible ahora!", inline=False)

        conn.close()

        if len(embed.fields) == 0:
            embed.description = "⚠️ No tienes ítems disponibles para recolectar."

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='collect', description='Recolecta tus ítems disponibles.')
async def collect(interaction: discord.Interaction):
    await interaction.response.defer()  # Evita que expire la interacción

    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    collected_amount = 0
    items_collected = []
    current_time = time.time()

    conn = await get_db_connection()
    async with conn.cursor() as c:
        user_roles = {str(role.id) for role in interaction.user.roles}

        # 1. Obtener todos los ítems de la tienda con rol requerido
        await c.execute('SELECT item_name, role_id, collect_amount, collect_interval FROM shop WHERE guild_id = %s', (guild_id,))
        shop_items = await c.fetchall()

        # 2. Verificar si el usuario tiene un rol que aún no esté registrado en collect_data
        for item_name, role_id, collect_amount, collect_interval in shop_items:
            if role_id in user_roles:
                await c.execute('''
                    SELECT 1 FROM collect_data 
                    WHERE guild_id = %s AND user_id = %s AND item_name = %s
                ''', (guild_id, user_id, item_name))
                exists = await c.fetchone()
                if not exists:
                    await c.execute('''
                        INSERT INTO collect_data (guild_id, user_id, item_name, last_collect, collect_amount, collect_interval)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (guild_id, user_id, item_name, 0, collect_amount, collect_interval))

        # 3. Obtener todos los ítems del usuario tras registrar los nuevos
        await c.execute('''
            SELECT item_name, last_collect, collect_amount, collect_interval 
            FROM collect_data 
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        user_items = await c.fetchall()

        for row in user_items:
            item_name, last_collect, collect_amount, collect_interval = row

            await c.execute('SELECT role_id FROM shop WHERE guild_id = %s AND item_name = %s',
                            (guild_id, item_name))
            role_required = await c.fetchone()

            if not role_required or role_required[0] not in user_roles:
                items_collected.append((item_name, 0))
                continue

            last_collect = last_collect if last_collect is not None else 0
            if last_collect == 0 or (current_time - last_collect >= collect_interval):
                await c.execute('''
                    UPDATE economy 
                    SET bank = bank + %s 
                    WHERE guild_id = %s AND user_id = %s
                ''', (collect_amount, guild_id, user_id))
                collected_amount += collect_amount

                await c.execute('''
                    UPDATE collect_data 
                    SET last_collect = %s 
                    WHERE guild_id = %s AND user_id = %s AND item_name = %s
                ''', (current_time, guild_id, user_id, item_name))

                items_collected.append((item_name, collect_amount))
            else:
                items_collected.append((item_name, 0))

        await conn.commit()
    conn.close()

    embed = discord.Embed(color=0x8A2BE2)
    embed.set_author(
        name=f"{interaction.user.name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
    )

    if collected_amount > 0:
        embed.description = f"<:Gringotts_Bank:1276368414528503858> **Notificación de Gringotts Bank**\n\nTus salarios han llegado a Gringotts Bank. Recibiste {collected_amount} <:Galeones:1276365877494677556>"
        collected_list = "\n".join(
            f"{i+1}- {item} | {amount} <:Galeones:1276365877494677556> (bank)"
            for i, (item, amount) in enumerate(items_collected)
            if amount > 0
        )
        embed.add_field(name="Detalles de la Recolección:", value=collected_list, inline=False)
    else:
        embed.description = "⚠️ No tienes ítems disponibles para recolectar en este momento."

    view = CollectView(user_id, guild_id, user_items, interaction.user)
    await interaction.followup.send(embed=embed, view=view)  # <- respuesta final

@bot.command(name='collect', aliases=['coll', 'colectar'])
async def collect(ctx):
    async with ctx.typing():
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        collected_amount = 0
        items_collected = []
        current_time = time.time()

        conn = await get_db_connection()
        async with conn.cursor() as c:
            user_roles = {str(role.id) for role in ctx.author.roles}

            # 1. Obtener ítems de la tienda con rol requerido
            await c.execute('SELECT item_name, role_id, collect_amount, collect_interval FROM shop WHERE guild_id = %s', (guild_id,))
            shop_items = await c.fetchall()

            # 2. Registrar ítems en collect_data si el usuario tiene el rol y aún no está
            for item_name, role_id, collect_amount, collect_interval in shop_items:
                if role_id in user_roles:
                    await c.execute('''
                        SELECT 1 FROM collect_data 
                        WHERE guild_id = %s AND user_id = %s AND item_name = %s
                    ''', (guild_id, user_id, item_name))
                    exists = await c.fetchone()
                    if not exists:
                        await c.execute('''
                            INSERT INTO collect_data (guild_id, user_id, item_name, last_collect, collect_amount, collect_interval)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (guild_id, user_id, item_name, 0, collect_amount, collect_interval))

            # 3. Obtener ítems del usuario
            await c.execute('''
                SELECT item_name, last_collect, collect_amount, collect_interval 
                FROM collect_data 
                WHERE guild_id = %s AND user_id = %s
            ''', (guild_id, user_id))
            user_items = await c.fetchall()

            for row in user_items:
                item_name, last_collect, collect_amount, collect_interval = row

                await c.execute('SELECT role_id FROM shop WHERE guild_id = %s AND item_name = %s',
                                (guild_id, item_name))
                role_required = await c.fetchone()

                if not role_required or role_required[0] not in user_roles:
                    items_collected.append((item_name, 0))
                    continue

                last_collect = last_collect if last_collect is not None else 0
                if last_collect == 0 or (current_time - last_collect >= collect_interval):
                    await c.execute('''
                        UPDATE economy 
                        SET bank = bank + %s 
                        WHERE guild_id = %s AND user_id = %s
                    ''', (collect_amount, guild_id, user_id))
                    collected_amount += collect_amount

                    await c.execute('''
                        UPDATE collect_data 
                        SET last_collect = %s 
                        WHERE guild_id = %s AND user_id = %s AND item_name = %s
                    ''', (current_time, guild_id, user_id, item_name))

                    items_collected.append((item_name, collect_amount))
                else:
                    items_collected.append((item_name, 0))

            await conn.commit()
        conn.close()

        embed = discord.Embed(color=0x8A2BE2)
        embed.set_author(
            name=f"{ctx.author.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        )

        if collected_amount > 0:
            embed.description = f"<:Gringotts_Bank:1276368414528503858> **Notificación de Gringotts Bank**\n\nTus salarios han llegado a Gringotts Bank. Recibiste {collected_amount} <:Galeones:1276365877494677556>"
            collected_list = "\n".join(
                f"{i+1}- {item} | {amount} <:Galeones:1276365877494677556> (bank)"
                for i, (item, amount) in enumerate(items_collected)
                if amount > 0
            )
            embed.add_field(name="Detalles de la Recolección:", value=collected_list, inline=False)
        else:
            embed.description = "⚠️ No tienes ítems disponibles para recolectar en este momento."

        view = CollectView(user_id, guild_id, user_items, ctx.author)
        await ctx.send(embed=embed, view=view)




@bot.command(name='buy')
async def buy_item(ctx, *item_name):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    item_name = ' '.join(item_name).lower()

    conn = await get_db_connection()
    async with conn.cursor() as c:
       
        await c.execute('SELECT item_name, price, collect_amount, collect_interval, role_id, is_available FROM shop WHERE guild_id = %s AND item_name = %s', (guild_id, item_name))
        item = await c.fetchone()

        if not item:
            await ctx.send(embed=create_embed(f"⚠️ El ítem `{item_name}` no existe en la tienda."))
            return

        item_name, price, collect_amount, collect_interval, role_id, is_available = item

       
        if is_available == 0:
            await ctx.send(embed=create_embed(f"⚠️ El ítem `{item_name}` no está disponible para la compra."))
            return

        
        await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        user_data = await c.fetchone()

        if not user_data:
           
            await c.execute('INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)', (guild_id, user_id, 0, 0))
            await conn.commit()
            coins = 0
        else:
            coins = user_data[0]

        if coins < price:
            await ctx.send(embed=create_embed(f"⚠️ No tienes suficientes monedas. Necesitas `{price}` monedas para comprar `{item_name}`."))
            return

        
        await c.execute('SELECT * FROM collect_data WHERE guild_id = %s AND user_id = %s AND item_name = %s', (guild_id, user_id, item_name))
        existing_item = await c.fetchone()

        if existing_item:
            await ctx.send(embed=create_embed(f"⚠️ Ya posees el ítem `{item_name}`. No puedes comprarlo nuevamente."))
            return

       
        new_balance = coins - price
        await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (new_balance, guild_id, user_id))
        await conn.commit()

       
        await c.execute('INSERT INTO collect_data (guild_id, user_id, item_name, last_collect, collect_amount, collect_interval) VALUES (%s, %s, %s, %s, %s, %s)', 
                        (guild_id, user_id, item_name, 0, collect_amount, collect_interval))
        await conn.commit()

       
        if role_id:
            role = ctx.guild.get_role(int(role_id))
            if role:
                await ctx.author.add_roles(role)
                await ctx.send(embed=create_embed(f"✅ Has comprado el ítem `{item_name}` por `{price}` <:Galeones:1276365877494677556>. ¡Ya puedes recolectar! Y se te ha asignado el rol `{role.name}`!"))
            else:
                await ctx.send(embed=create_embed(f"✅ Has comprado el ítem `{item_name}` por `{price}` <:Galeones:1276365877494677556>. ¡Ya puedes recolectar! Pero el rol no se encontró."))
        else:
            await ctx.send(embed=create_embed(f"✅ Has comprado el ítem `{item_name}` por `{price}` <:Galeones:1276365877494677556>. ¡Ya puedes recolectar! Pero no se asignó ningún rol."))
    conn.close()


def create_embed(description):
    embed = discord.Embed(description=description, color=0x00ff00)
    return embed


@bot.tree.command(name='buy', description='Compra un ítem de la tienda.')
@app_commands.describe(item_name='Nombre del ítem que deseas comprar')
async def buy_item(interaction: discord.Interaction, item_name: str):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    item_name = item_name.lower()

    conn = await get_db_connection()
    async with conn.cursor() as c:

        await c.execute('SELECT item_name, price, collect_amount, collect_interval, role_id, is_available FROM shop WHERE guild_id = %s AND item_name = %s', (guild_id, item_name))
        item = await c.fetchone()

        if not item:
            await interaction.response.send_message(embed=create_embed(f"⚠️ El ítem `{item_name}` no existe en la tienda."))
            return

        item_name, price, collect_amount, collect_interval, role_id, is_available = item

   
        if is_available == 0:
            await interaction.response.send_message(embed=create_embed(f"⚠️ El ítem `{item_name}` no está disponible para la compra."))
            return

   
        await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
        user_data = await c.fetchone()

        if not user_data:
         
            await c.execute('INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)', (guild_id, user_id, 0, 0))
            await conn.commit()
            coins = 0
        else:
            coins = user_data[0]

        if coins < price:
            await interaction.response.send_message(embed=create_embed(f"⚠️ No tienes suficientes monedas. Necesitas `{price}` monedas para comprar `{item_name}`."))
            return

      
        await c.execute('SELECT * FROM collect_data WHERE guild_id = %s AND user_id = %s AND item_name = %s', (guild_id, user_id, item_name))
        existing_item = await c.fetchone()

        if existing_item:
            await interaction.response.send_message(embed=create_embed(f"⚠️ Ya posees el ítem `{item_name}`. No puedes comprarlo nuevamente."))
            return

     
        new_balance = coins - price
        await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (new_balance, guild_id, user_id))
        await conn.commit()

   
        await c.execute('INSERT INTO collect_data (guild_id, user_id, item_name, last_collect, collect_amount, collect_interval) VALUES (%s, %s, %s, %s, %s, %s)', 
                        (guild_id, user_id, item_name, 0, collect_amount, collect_interval))
        await conn.commit()

      
        if role_id:
            role = interaction.guild.get_role(int(role_id))
            if role:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(embed=create_embed(f"✅ Has comprado el ítem `{item_name}` por `{price}` <:Galeones:1276365877494677556>. ¡Ya puedes recolectar! Y se te ha asignado el rol `{role.name}`!"))
            else:
                await interaction.response.send_message(embed=create_embed(f"✅ Has comprado el ítem `{item_name}` por `{price}` <:Galeones:1276365877494677556>. ¡Ya puedes recolectar! Pero el rol no se encontró."))
        else:
            await interaction.response.send_message(embed=create_embed(f"✅ Has comprado el ítem `{item_name}` por `{price}` <:Galeones:1276365877494677556>. ¡Ya puedes recolectar! Pero no se asignó ningún rol."))
    conn.close()


@bot.tree.command(name='take-item', description='Quita un ítem a un usuario.')
@app_commands.describe(member="El usuario al que se le quitará el ítem", item_name="Nombre del ítem a quitar")
async def take_item(interaction: discord.Interaction, member: discord.Member, item_name: str):
    # Verificar si el usuario que invoca el comando tiene permisos de administrador
    if not interaction.user.guild_permissions.manage_roles:
        embed = discord.Embed(
            title="Permiso denegado",
            description="No tienes permiso para usar este comando.",
            color=0x8A2BE2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    user_id = str(member.id)  # ID del usuario al que se le quita el ítem

    # Convertir el nombre del ítem a minúsculas
    item_name = item_name.lower()

    # Obtener conexión a la base de datos
    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Buscar el ítem en la tabla collect_data en MySQL
        await c.execute('SELECT * FROM collect_data WHERE guild_id = %s AND user_id = %s AND item_name = %s', (guild_id, user_id, item_name))
        existing_item = await c.fetchone()

        if not existing_item:
            embed = discord.Embed(
                title="Ítem no encontrado",
                description=f"⚠️ El usuario `{member}` no posee el ítem `{item_name}`.",
                color=0x8A2BE2
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Obtener el role_id asociado al ítem
        await c.execute('SELECT role_id FROM shop WHERE guild_id = %s AND item_name = %s', (guild_id, item_name))
        role_data = await c.fetchone()

        if role_data:
            role_id = role_data[0]
            role = interaction.guild.get_role(int(role_id))  # Convertir a entero

            # Quitar el rol al usuario
            if role:
                await member.remove_roles(role)
                embed = discord.Embed(
                    title="Ítem quitado",
                    description=f"✅ Se le ha quitado el ítem `{item_name}` a `{member}` y se le ha removido el rol `{role.name}`.",
                    color=0x8A2BE2
                )
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(
                    title="Rol no encontrado",
                    description=f"✅ Se le ha quitado el ítem `{item_name}` a `{member}`, pero el rol no se encontró.",
                    color=0x8A2BE2
                )
                await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="Rol no asociado",
                description=f"✅ Se le ha quitado el ítem `{item_name}` a `{member}`, pero no se puede encontrar el rol asociado.",
                color=0x8A2BE2
            )
            await interaction.response.send_message(embed=embed)

        # Eliminar el ítem de la tabla collect_data
        await c.execute('DELETE FROM collect_data WHERE guild_id = %s AND user_id = %s AND item_name = %s', (guild_id, user_id, item_name))
        await conn.commit()

    conn.close()  # Cerrar la conexión

@bot.command(name='shop')
async def shop(ctx):
    guild_id = str(ctx.guild.id)

    # Obtener una conexión a la base de datos MySQL
    async with await get_db_connection() as conn:
        async with conn.cursor() as c:
            # Recuperar solo los ítems disponibles de la base de datos (tabla `shop`)
            await c.execute('SELECT item_name, price, description, role_id FROM shop WHERE guild_id = %s AND is_available = 1', (guild_id,))
            shop_items = await c.fetchall()

    if not shop_items:
        await ctx.send(embed=create_embed("📦 La tienda está vacía actualmente."))
        return

    # Ordenar los ítems por precio de menor a mayor
    sorted_shop_items = sorted(shop_items, key=lambda x: x[1])

    # Número de artículos por página
    items_per_page = 3
    total_pages = (len(sorted_shop_items) - 1) // items_per_page + 1

    # URL de la imagen de Diagon Alley
    diagon_alley_image_url = "https://cdn.discordapp.com/attachments/1277162414877573242/1283110090790146192/desktop-wallpaper-the-wizarding-world-of-harry-potter-harry-potter-diagon-alley.png?ex=66e1cce4&is=66e07b64&hm=e425f11863efa76ffc308140aeb8def6a681ae2f4b7e2f6185a5ed7aa4ee5c9a&"

    async def generate_embed(page):
        embed = discord.Embed(title="🛒 Callejón Diagon", color=discord.Color.purple())

        # Agregar la imagen de Diagon Alley
        embed.set_thumbnail(url=diagon_alley_image_url)

        # Explicación de cómo comprar un artículo
        embed.description = "Para comprar un artículo, use el comando `$buy <nombre del item>`.\n\n"

        # Obtener el rango de artículos para la página actual
        start = page * items_per_page
        end = start + items_per_page
        for item_name, price, description, role_id in sorted_shop_items[start:end]:
            role = f"<@&{role_id}>" if role_id else "Ninguno"
            embed.add_field(
                name=f"{item_name} - {price:,} <:Galeones:1276365877494677556>",
                value=f"**Descripción:** {description}\n**Rol Otorgado:** {role}\n\n--------------------",
                inline=False
            )

        # Agregar el nombre y la imagen de perfil del servidor en el pie de página
        guild_icon_url = ctx.guild.icon.url if ctx.guild.icon else None
        embed.set_footer(text=f"Página {page + 1}/{total_pages} • {ctx.guild.name}", icon_url=guild_icon_url)
        return embed

    # Función para actualizar el mensaje con la nueva página
    async def update_shop_page(interaction, page):
        if interaction.user != ctx.author:  # Verificar que solo el autor pueda usar los botones
            await interaction.response.send_message("<:Hermyerror:1282524139135045642>  No puedes interactuar con este menú, si deseas ver la tienda utiliza $shop.", ephemeral=True)
            return

        embed = await generate_embed(page)
        await interaction.response.edit_message(embed=embed, view=create_shop_view(page))

    # Crear los botones de navegación
    def create_shop_view(page):
        view = View()

        # Botón de página anterior
        prev_button = Button(label="Página anterior", style=discord.ButtonStyle.grey, disabled=page == 0)
        async def prev_callback(interaction):
            await update_shop_page(interaction, page - 1)
        prev_button.callback = prev_callback

        # Botón de página siguiente
        next_button = Button(label="Página siguiente", style=discord.ButtonStyle.grey, disabled=page == total_pages - 1)
        async def next_callback(interaction):
            await update_shop_page(interaction, page + 1)
        next_button.callback = next_callback

        view.add_item(prev_button)
        view.add_item(next_button)
        return view

    # Enviar el primer mensaje con la página inicial
    page = 0
    embed = await generate_embed(page)
    view = create_shop_view(page)
    await ctx.send(embed=embed, view=view)

@bot.tree.command(name="server-shop", description="Muestra los ítems disponibles en la tienda del servidor.")
async def server_shop(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)

    # Obtener una conexión a la base de datos MySQL
    async with await get_db_connection() as conn:
        async with conn.cursor() as c:
            # Recuperar solo los ítems disponibles de la base de datos (tabla `shop`)
            await c.execute('SELECT item_name, price, description, role_id FROM shop WHERE guild_id = %s AND is_available = 1', (guild_id,))
            shop_items = await c.fetchall()

    if not shop_items:
        await interaction.response.send_message(embed=create_embed("📦 La tienda está vacía actualmente."), ephemeral=True)
        return

    # Ordenar los ítems por precio de menor a mayor
    sorted_shop_items = sorted(shop_items, key=lambda x: x[1])

    # Número de artículos por página
    items_per_page = 3
    total_pages = (len(sorted_shop_items) - 1) // items_per_page + 1

    # URL de la imagen de Diagon Alley
    diagon_alley_image_url = "https://cdn.discordapp.com/attachments/1277162414877573242/1283110090790146192/desktop-wallpaper-the-wizarding-world-of-harry-potter-harry-potter-diagon-alley.png?ex=66e1cce4&is=66e07b64&hm=e425f11863efa76ffc308140aeb8def6a681ae2f4b7e2f6185a5ed7aa4ee5c9a&"

    async def generate_embed(page):
        embed = discord.Embed(title="🛒 Callejón Diagon", color=discord.Color.purple())

        # Agregar la imagen de Diagon Alley
        embed.set_thumbnail(url=diagon_alley_image_url)

        # Explicación de cómo comprar un artículo
        embed.description = "Para comprar un artículo, use el comando `/buy <nombre del item>`.\n\n"

        # Obtener el rango de artículos para la página actual
        start = page * items_per_page
        end = start + items_per_page
        for item_name, price, description, role_id in sorted_shop_items[start:end]:
            role = f"<@&{role_id}>" if role_id else "Ninguno"
            embed.add_field(
                name=f"{item_name} - {price:,} <:Galeones:1276365877494677556>",
                value=f"**Descripción:** {description}\n**Rol Otorgado:** {role}\n\n--------------------",
                inline=False
            )

        # Agregar el nombre y la imagen de perfil del servidor en el pie de página
        guild_icon_url = interaction.guild.icon.url if interaction.guild.icon else None
        embed.set_footer(text=f"Página {page + 1}/{total_pages} • {interaction.guild.name}", icon_url=guild_icon_url)
        return embed

    # Función para actualizar el mensaje con la nueva página
    async def update_shop_page(interaction, page):
        if interaction.user != interaction.user:  # Verificar que solo el autor pueda usar los botones
            await interaction.response.send_message("<:Hermyerror:1282524139135045642>  No puedes interactuar con este menú, si deseas ver la tienda utiliza /server-shop.", ephemeral=True)
            return

        embed = await generate_embed(page)
        await interaction.response.edit_message(embed=embed, view=create_shop_view(page))

    # Crear los botones de navegación
    def create_shop_view(page):
        view = discord.ui.View()

        # Botón de página anterior
        prev_button = discord.ui.Button(label="Página anterior", style=discord.ButtonStyle.grey, disabled=page == 0)
        async def prev_callback(interaction):
            await update_shop_page(interaction, page - 1)
        prev_button.callback = prev_callback

        # Botón de página siguiente
        next_button = discord.ui.Button(label="Página siguiente", style=discord.ButtonStyle.grey, disabled=page == total_pages - 1)
        async def next_callback(interaction):
            await update_shop_page(interaction, page + 1)
        next_button.callback = next_callback

        view.add_item(prev_button)
        view.add_item(next_button)
        return view

    # Enviar el primer mensaje con la página inicial
    page = 0
    embed = await generate_embed(page)
    view = create_shop_view(page)
    await interaction.response.send_message(embed=embed, view=view)



@bot.command(name="inventory", description="Muestra el inventario del usuario")
async def inventory(ctx):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    # Obtener conexión a la base de datos
    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Obtener ítems recolectados por el usuario
        await c.execute('''
            SELECT item_name, last_collect
            FROM collect_data
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        collected_items = {row[0] for row in await c.fetchall()}

        # Obtener ítems de la tienda y verificar roles
        await c.execute('''
            SELECT item_name, price, collect_amount, collect_interval, role_id
            FROM shop
            WHERE guild_id = %s
        ''', (guild_id,))
        shop_items = await c.fetchall()

        user_items = []
        for item_name, price, collect_amount, collect_interval, rol_id in shop_items:
            # Si el ítem ya está en el inventario o el usuario tiene el rol requerido
            if item_name in collected_items or (rol_id and discord.utils.get(ctx.author.roles, id=int(rol_id))):
                user_items.append({
                    'item_name': item_name,
                    'price': price,
                    'collect_amount': collect_amount,
                    'collect_interval': collect_interval
                })

    conn.close()

    # Si no tiene ítems, enviar mensaje
    if not user_items:
        await ctx.send(embed=create_embed("📦 No tienes ítems válidos en el inventario actualmente."))
        return

    # Ordenar los ítems por precio de mayor a menor
    user_items.sort(key=lambda x: x['price'], reverse=True)

    items_per_page = 3
    total_pages = (len(user_items) + items_per_page - 1) // items_per_page

    def format_collect_time(seconds):
        if seconds is None:
            return "No disponible"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} horas, {minutes} minutos" if hours > 0 else f"{minutes} minutos"

    async def generate_embed(page):
        embed = discord.Embed(
            title=f"Inventario de {ctx.author.display_name}",
            description="Estos son los ítems disponibles:",
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1277162414877573242/1283116799986110567/inventory_11000448.png")

        start, end = page * items_per_page, (page + 1) * items_per_page
        for item in user_items[start:end]:
            embed.add_field(
                name=f"🔹 {item['item_name']}",
                value=f"**Valor:** `{item['price']:,}` <:Galeones:1276365877494677556>\n"
                      f"**Recompensa:** `{item['collect_amount']:,}` <:Galeones:1276365877494677556>\n"
                      f"**Tiempo:** `{format_collect_time(item['collect_interval'])}`",
                inline=False
            )

        avatar_url = ctx.author.avatar.url if ctx.author.avatar else 'https://example.com/default-avatar.png'
        embed.set_footer(text=f"Página {page + 1}/{total_pages} • Inventario de {ctx.author.display_name}",
                         icon_url=avatar_url)
        return embed

    async def update_inventory_page(interaction, page):
        embed = await generate_embed(page)
        await interaction.response.edit_message(embed=embed, view=create_inventory_view(page))

    def create_inventory_view(page):
        view = View()

        if total_pages > 1:
            prev_button = Button(label="Página anterior", style=discord.ButtonStyle.grey, disabled=page == 0)
            async def prev_callback(interaction: discord.Interaction):
                await update_inventory_page(interaction, page - 1)
            prev_button.callback = prev_callback
            view.add_item(prev_button)

            next_button = Button(label="Página siguiente", style=discord.ButtonStyle.grey, disabled=page == total_pages - 1)
            async def next_callback(interaction: discord.Interaction):
                await update_inventory_page(interaction, page + 1)
            next_button.callback = next_callback
            view.add_item(next_button)

        return view

    page = 0
    embed = await generate_embed(page)
    view = create_inventory_view(page)
    await ctx.send(embed=embed, view=view)

def create_embed(message):
    embed = discord.Embed(description=message, color=discord.Color.red())
    return embed



@bot.tree.command(name="inventory", description="Muestra el inventario del usuario")
async def inventory(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    # Obtener la conexión a la base de datos
    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Consultar la base de datos para obtener los ítems recolectados por el usuario
        await c.execute('''
            SELECT item_name, last_collect
            FROM collect_data
            WHERE guild_id = %s AND user_id = %s
        ''', (guild_id, user_id))
        collected_items = await c.fetchall()

        if not collected_items:
            await interaction.response.send_message(embed=create_embed("📦 No tienes ítems en el inventario actualmente."))
            return

        # Crear una lista para almacenar los detalles de los ítems del inventario
        user_items = []

        # Consultar la tabla 'shop' para obtener los detalles de los ítems
        for item_name, last_collect in collected_items:
            await c.execute('''
                SELECT price, collect_amount, collect_interval
                FROM shop
                WHERE guild_id = %s AND item_name = %s
            ''', (guild_id, item_name))
            item_details = await c.fetchone()

            if item_details:
                price, collect_amount, collect_interval = item_details
                user_items.append({
                    'item_name': item_name,
                    'price': price,
                    'collect_amount': collect_amount,
                    'collect_interval': collect_interval
                })

    # Cerrar la conexión después de la consulta
    conn.close()

    # Si no hay ítems encontrados en la tienda
    if not user_items:
        await interaction.response.send_message(embed=create_embed("📦 No tienes ítems válidos en el inventario actualmente."))
        return

    # Ordenar los ítems por precio de mayor a menor
    user_items.sort(key=lambda x: x['price'], reverse=True)

    # Número de artículos por página
    items_per_page = 3
    total_pages = (len(user_items) + items_per_page - 1) // items_per_page

    # Función para formatear el tiempo de collect
    def format_collect_time(seconds):
        if seconds is None:
            return "No disponible"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours} horas, {minutes} minutos"
        else:
            return f"{minutes} minutos"

    async def generate_embed(page):
        embed = discord.Embed(
            title=f"Inventario de {interaction.user.display_name}",
            description="Estos son los ítems disponibles:",
            color=discord.Color.purple()  # Color violeta
        )

        # Agregar la imagen del inventario
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1277162414877573242/1283116799986110567/inventory_11000448.png")

        # Obtener el rango de artículos para la página actual
        start = page * items_per_page
        end = start + items_per_page

        for item in user_items[start:end]:
            collect_time_formatted = format_collect_time(item['collect_interval'])
            embed.add_field(
                name=f"🔹 {item['item_name']}",
                value=f"**Valor:** `{item['price']:,}`<:Galeones:1276365877494677556>\n"
                      f"**Recompensa por collect:** `{item['collect_amount']:,}`<:Galeones:1276365877494677556>\n"
                      f"**Tiempo de collect:** `{collect_time_formatted}`",
                inline=False
            )

        if not user_items[start:end]:
            embed.description = "No tienes ítems en el inventario."

        # Añadir la imagen de perfil y el nombre del usuario al final del embed
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else 'https://example.com/default-avatar.png'
        embed.set_footer(
            text=f"Página {page + 1}/{total_pages} • {interaction.user.display_name}'s inventory",
            icon_url=avatar_url
        )

        return embed

    # Función para actualizar el mensaje con la nueva página
    async def update_inventory_page(interaction, page):
        if interaction.user != interaction.user:  # Verificar que solo el autor pueda usar los botones
            await interaction.response.send_message("No puedes interactuar con este menú.", ephemeral=True)
            return
        
        embed = await generate_embed(page)
        await interaction.response.edit_message(embed=embed, view=create_inventory_view(page))

    # Crear los botones de navegación
    def create_inventory_view(page):
        view = View()

        # Botón de página anterior
        if total_pages > 1:
            prev_button = Button(label="Página anterior", style=discord.ButtonStyle.grey, disabled=page == 0)
            async def prev_callback(interaction):
                await update_inventory_page(interaction, page - 1)
            prev_button.callback = prev_callback
            view.add_item(prev_button)

            # Botón de página siguiente
            next_button = Button(label="Página siguiente", style=discord.ButtonStyle.grey, disabled=page == total_pages - 1)
            async def next_callback(interaction):
                await update_inventory_page(interaction, page + 1)
            next_button.callback = next_callback
            view.add_item(next_button)

        return view

    # Enviar el primer mensaje con la página inicial
    page = 0
    embed = await generate_embed(page)
    view = create_inventory_view(page)
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name='give-item', description='Otorga un ítem a un usuario.')
@app_commands.describe(user="Usuario al que se le dará el ítem", item_name="Nombre del ítem a otorgar")
async def give_item(interaction: discord.Interaction, user: discord.Member, item_name: str):
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            description="No tienes permiso para usar este comando.",
            color=0x8A2BE2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    guild_id = str(interaction.guild.id)
    user_id = str(user.id)

    # Obtener conexión a la base de datos
    conn = await get_db_connection()
    
    if conn is None:
        await interaction.response.send_message(embed=create_embed("❌ No se pudo conectar a la base de datos."), ephemeral=True)
        return

    try:
        async with conn.cursor() as c:
            # Obtener el ítem de la tienda
            await c.execute('SELECT item_name, price, collect_amount, collect_interval, role_id FROM shop WHERE guild_id = %s AND item_name = %s', (guild_id, item_name.lower()))
            item = await c.fetchone()

            if not item:
                await interaction.response.send_message(embed=create_embed(f"⚠️ El ítem `{item_name}` no existe en la tienda.", color=0x00FF00))
                return

            item_name, price, collect_amount, collect_interval, role_id = item

            # Verificar si el usuario ya tiene el ítem
            await c.execute('SELECT * FROM collect_data WHERE guild_id = %s AND user_id = %s AND item_name = %s', (guild_id, user_id, item_name.lower()))
            existing_item = await c.fetchone()

            if existing_item:
                await interaction.response.send_message(embed=create_embed(f"⚠️ El usuario `{user.display_name}` ya tiene el ítem `{item_name}`.", color=0x00FF00))
                return

            # Insertar el ítem en la tabla collect_data
            await c.execute(
                'INSERT INTO collect_data (guild_id, user_id, item_name, last_collect, collect_amount, collect_interval) VALUES (%s, %s, %s, %s, %s, %s)', 
                (guild_id, user_id, item_name.lower(), 0, collect_amount, collect_interval)
            )

            await conn.commit()

            # Otorgar el rol si está asociado con el ítem
            if role_id:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    await user.add_roles(role)
                    await interaction.response.send_message(embed=create_embed(f"🎁 Has dado el ítem `{item_name}` al usuario `{user.display_name}`. También se le otorgó el rol `{role.name}`.", color=0x00FF00))
                else:
                    await interaction.response.send_message(embed=create_embed(f"🎁 Has dado el ítem `{item_name}` al usuario `{user.display_name}`, pero no se pudo encontrar el rol asignado.", color=0x00FF00))
            else:
                await interaction.response.send_message(embed=create_embed(f"🎁 Has dado el ítem `{item_name}` al usuario `{user.display_name}`.", color=0x00FF00))

    finally:
        if conn is not None:
            conn.close()  # no usar await aquí si `conn.close()` no es async


apuestas_activas = {}

@bot.tree.command(name="ruleta", description="Haz una apuesta en la ruleta mágica")
@app_commands.describe(apuesta="Elige número (0-36), rojo, negro, par o impar", cantidad="Cantidad de monedas a apostar")
async def ruleta(interaction: discord.Interaction, apuesta: str, cantidad: str):
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    # Verificar si el usuario ya tiene una apuesta activa en este servidor
    if guild_id in apuestas_activas and user_id in apuestas_activas[guild_id]:
        embed = discord.Embed(
            title="⚠️ Apuesta en curso",
            description=f"{interaction.user.mention}, ya tienes una apuesta en curso. Espera a que termine antes de hacer otra.",
            color=0xFF0000
        )
        avatar_url = interaction.user.avatar.url if interaction.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        embed.set_author(name=f"{interaction.user.name}", icon_url=avatar_url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Conectar a la base de datos
    conn = await get_db_connection()
    try:
        async with conn.cursor() as c:
            await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
            user_data = await c.fetchone()

            if user_data is None:
                await interaction.response.send_message("⚠️ No tienes un registro en el sistema. Por favor, gana o recibe algún ítem primero.", ephemeral=True)
                return

            saldo_actual = user_data[0]

            # Validación de argumentos
            valid_apuestas = ['rojo', 'negro', 'par', 'impar'] + [str(i) for i in range(37)]
            if apuesta.lower() not in valid_apuestas:
                embed = discord.Embed(
                    title="<:Hermyerror:1282524139135045642>",
                    description="Apuesta no válida. Debes elegir un número entre 0-36, 'rojo', 'negro', 'par' o 'impar'.",
                    color=0x8A2BE2
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if cantidad.lower() == 'all':
                cantidad = saldo_actual
            else:
                try:
                    cantidad = int(cantidad)
                except ValueError:
                    embed = discord.Embed(
                        title="<:Hermyerror:1282524139135045642>",
                        description="La cantidad debe ser un número o 'all'.",
                        color=0x8A2BE2
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

            if cantidad <= 0 or cantidad > saldo_actual:
                embed = discord.Embed(
                    title="<:Hermyerror:1282524139135045642>",
                    description="La cantidad debe ser positiva y menor o igual a tu saldo.",
                    color=0x8A2BE2
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Registrar la apuesta
            cantidad_apostada = cantidad
            if guild_id not in apuestas_activas:
                apuestas_activas[guild_id] = {}
            apuestas_activas[guild_id][user_id] = cantidad_apostada
            nuevo_saldo = saldo_actual - cantidad
            await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (nuevo_saldo, guild_id, user_id))
            await conn.commit()

    finally:
        conn.close()

    finaliza_en = int((datetime.now(timezone.utc) + timedelta(seconds=1)).timestamp())
    embed = discord.Embed(
        title="<a:Wlingeconomia:1280184712136228972>  *Casino Mágico*",
        description=(f"Realizando el giro... Finalizará en: <t:{finaliza_en}:R>\n"
                     f"Apuesta: `{cantidad_apostada}` <:Galeones:1276365877494677556>\n"
                     f"Apostaste a: `{apuesta}`"),
        color=0x8A2BE2
    )
    avatar_url = interaction.user.avatar.url if interaction.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
    embed.set_author(name=f"{interaction.user.name}", icon_url=avatar_url)

    # Envía el primer mensaje de respuesta
    await interaction.response.send_message(embed=embed)

    await asyncio.sleep(30)

    colores = ['rojo', 'negro']
    numeros = list(range(37))
    resultado_numero = random.choice(numeros)
    resultado_color = colores[resultado_numero % 2]
    es_par = resultado_numero % 2 == 0
    resultado_visual = ":green_circle: 0" if resultado_numero == 0 else (
        f"{':red_circle:' if resultado_color == 'rojo' else ':black_circle:'} {resultado_numero}")

    ganar = False
    mensaje = ""
    ganancias = 0

    if apuesta.isdigit() and int(apuesta) == resultado_numero:
        ganar = True
        ganancias = cantidad_apostada * 36
        mensaje = f"¡Felicidades! Ganaste `{ganancias}` <:Galeones:1276365877494677556>."
    elif apuesta in colores and apuesta == resultado_color:
        ganar = True
        ganancias = cantidad_apostada * 2
        mensaje = f"¡Felicidades! Ganaste `{ganancias}` <:Galeones:1276365877494677556>."
    elif apuesta in ['par', 'impar'] and ((apuesta == 'par' and es_par) or (apuesta == 'impar' and not es_par)):
        ganar = True
        ganancias = cantidad_apostada * 2
        mensaje = f"¡Felicidades! Ganaste `{ganancias}` <:Galeones:1276365877494677556>."
    else:
        mensaje = "Perdiste."

    if ganar:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as c:
                await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
                saldo_actual = (await c.fetchone())[0]
                saldo_actualizado = saldo_actual + ganancias
                await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (saldo_actualizado, guild_id, user_id))
                await conn.commit()
        finally:
            conn.close()

    del apuestas_activas[guild_id][user_id]
    embed_color = 0x00FF00 if ganar else 0xFF0000
    embed = discord.Embed(
        title="<:Wlingrulete:1279332590343421994>  *Casino Mágico*",
        description=f"{mensaje}\n\nNúmero final: ┋{resultado_visual}┋\nApuesta realizada: `{cantidad_apostada}` <:Galeones:1276365877494677556>",
        color=embed_color
    )
    embed.set_author(name=f"{interaction.user.name}", icon_url=avatar_url)
    # Envía el resultado final en un nuevo mensaje
    await interaction.followup.send(embed=embed)

@bot.command(name="ruleta", help="Haz una apuesta en la ruleta mágica")
async def ruleta(ctx, apuesta: str, cantidad: str):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)

    # Verificar si el usuario ya tiene una apuesta activa en este servidor
    if guild_id in apuestas_activas and user_id in apuestas_activas[guild_id]:
        embed = discord.Embed(
            title="⚠️ Apuesta en curso",
            description=f"{ctx.author.mention}, ya tienes una apuesta en curso. Espera a que termine antes de hacer otra.",
            color=0xFF0000
        )
        avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        embed.set_author(name=f"{ctx.author.name}", icon_url=avatar_url)
        await ctx.send(embed=embed)
        return

    # Conectar a la base de datos
    conn = await get_db_connection()
    try:
        async with conn.cursor() as c:
            await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
            user_data = await c.fetchone()

            if user_data is None:
                await ctx.send("⚠️ No tienes un registro en el sistema. Por favor, gana o recibe algún ítem primero.")
                return

            saldo_actual = user_data[0]

            # Validación de argumentos
            valid_apuestas = ['rojo', 'negro', 'par', 'impar'] + [str(i) for i in range(37)]
            if apuesta.lower() not in valid_apuestas:
                embed = discord.Embed(
                    title="<:Hermyerror:1282524139135045642>",
                    description="Apuesta no válida. Debes elegir un número entre 0-36, 'rojo', 'negro', 'par' o 'impar'.",
                    color=0x8A2BE2
                )
                await ctx.send(embed=embed)
                return

            if cantidad.lower() == 'all':
                cantidad = saldo_actual
            else:
                try:
                    cantidad = int(cantidad)
                except ValueError:
                    embed = discord.Embed(
                        title="<:Hermyerror:1282524139135045642>",
                        description="La cantidad debe ser un número o 'all'.",
                        color=0x8A2BE2
                    )
                    await ctx.send(embed=embed)
                    return

            if cantidad <= 0 or cantidad > saldo_actual:
                embed = discord.Embed(
                    title="<:Hermyerror:1282524139135045642>",
                    description="La cantidad debe ser positiva y menor o igual a tu saldo.",
                    color=0x8A2BE2
                )
                await ctx.send(embed=embed)
                return

            # Registrar la apuesta
            cantidad_apostada = cantidad
            if guild_id not in apuestas_activas:
                apuestas_activas[guild_id] = {}
            apuestas_activas[guild_id][user_id] = cantidad_apostada
            nuevo_saldo = saldo_actual - cantidad
            await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (nuevo_saldo, guild_id, user_id))
            await conn.commit()

    finally:
        conn.close()

    finaliza_en = int((datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp())
    embed = discord.Embed(
        title="<a:Wlingeconomia:1280184712136228972>  *Casino Mágico*",
        description=(f"Realizando el giro... Finalizará en: <t:{finaliza_en}:R>\n"
                     f"Apuesta: `{cantidad_apostada}` <:Galeones:1276365877494677556>\n"
                     f"Apostaste a: `{apuesta}`"),
        color=0x8A2BE2
    )
    avatar_url = ctx.author.avatar.url if ctx.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
    embed.set_author(name=f"{ctx.author.name}", icon_url=avatar_url)

    await ctx.send(embed=embed)
    await asyncio.sleep(30)

    colores = ['rojo', 'negro']
    numeros = list(range(37))
    resultado_numero = random.choice(numeros)
    resultado_color = colores[resultado_numero % 2]
    es_par = resultado_numero % 2 == 0
    resultado_visual = ":green_circle: 0" if resultado_numero == 0 else (
        f"{':red_circle:' if resultado_color == 'rojo' else ':black_circle:'} {resultado_numero}")

    ganar = False
    mensaje = ""
    ganancias = 0

    if apuesta.isdigit() and int(apuesta) == resultado_numero:
        ganar = True
        ganancias = cantidad_apostada * 36
        mensaje = f"¡Felicidades! Ganaste `{ganancias}` <:Galeones:1276365877494677556>."
    elif apuesta in colores and apuesta == resultado_color:
        ganar = True
        ganancias = cantidad_apostada * 2
        mensaje = f"¡Felicidades! Ganaste `{ganancias}` <:Galeones:1276365877494677556>."
    elif apuesta in ['par', 'impar'] and ((apuesta == 'par' and es_par) or (apuesta == 'impar' and not es_par)):
        ganar = True
        ganancias = cantidad_apostada * 2
        mensaje = f"¡Felicidades! Ganaste `{ganancias}` <:Galeones:1276365877494677556>."
    else:
        mensaje = "Perdiste."

    if ganar:
        conn = await get_db_connection()
        try:
            async with conn.cursor() as c:
                await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
                saldo_actual = (await c.fetchone())[0]
                saldo_actualizado = saldo_actual + ganancias
                await c.execute('UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s', (saldo_actualizado, guild_id, user_id))
                await conn.commit()
        finally:
            conn.close()

    del apuestas_activas[guild_id][user_id]
    embed_color = 0x00FF00 if ganar else 0xFF0000
    embed = discord.Embed(
        title="<:Wlingrulete:1279332590343421994>  *Casino Mágico*",
        description=f"{mensaje}\n\nNúmero final: ┋{resultado_visual}┋\nApuesta realizada: `{cantidad_apostada}` <:Galeones:1276365877494677556>",
        color=embed_color
    )
    embed.set_author(name=f"{ctx.author.name}", icon_url=avatar_url)

    await ctx.send(embed=embed)

cartas_emojis = {
    'A': '<:HermyBJA:1286125257039675423>',
    '2': '<:HermyBJ2:1286126194516824087>',
    '3': '<:HermyBJ3:1286124903698796627>',
    '4': '<:HermyBJ4:1286125960462073877>',
    '5': '<:HermyBJ5:1286125508010049610>',
    '6': '<:HermyBJ6:1286126740472725536>',
    '7': '<:HermyBJ7:1286126868889731136>',
    '8': '<:HermyBJ8:1286127005896675328>',
    '9': '<:HermyBJ9:1286125077493973084>',
    '10': '<:HermyBJ10:1286127112079544411>',
    'J': '<:HermyBJJ:1286127302878433341>',
    'Q': '<:HermyBJQ:1286124763932135467>',
    'K': '<:HermyBJK:1286127496894615563>'
}

def calculate_hand_value(hand): 
    value = sum(11 if card == 'A' else 10 if card in ['J', 'Q', 'K'] else int(card) for card in hand)
    aces = hand.count('A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

@bot.tree.command(name='blackjack', description='Juega al Blackjack y apuesta una cantidad de monedas.')
@app_commands.describe(cantidad='Cantidad a apostar. Usa "all" para apostar toda tu cantidad.')
async def blackjack(interaction: discord.Interaction, cantidad: str):
    guild_id, user_id = str(interaction.guild.id), str(interaction.user.id)

    # Obtener conexión a la base de datos
    conn = await get_db_connection()
    async with conn.cursor() as c:
        # Obtener datos del usuario de la base de datos
        await c.execute("SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()
        
        if result is None:
            # Si el usuario no existe, inicializar en 0
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", (guild_id, user_id, 0, 0))
            await conn.commit()
            user_coins = 0
        else:
            user_coins = result[0]

        # Verificar si se proporciona la cantidad a apostar
        if not cantidad:
            return await interaction.response.send_message("Por favor, proporciona la cantidad a apostar.", ephemeral=True)

        # Si el argumento es 'all', apostar toda la cantidad de dinero
        if cantidad.lower() == 'all':
            if user_coins <= 0:
                return await interaction.response.send_message("No tienes suficiente efectivo para apostar toda tu cantidad.", ephemeral=True)
            cantidad = user_coins
        else:
            try:
                cantidad = int(cantidad)
            except ValueError:
                return await interaction.response.send_message("La cantidad especificada no es válida.", ephemeral=True)

        if cantidad <= 0:
            return await interaction.response.send_message("La cantidad a apostar debe ser mayor que cero.", ephemeral=True)

        if cantidad > user_coins:
            return await interaction.response.send_message("No tienes suficientes Galeones.", ephemeral=True)

        # Restar la apuesta
        await c.execute("UPDATE economy SET coins = coins - %s WHERE guild_id = %s AND user_id = %s", (cantidad, guild_id, user_id))
        await conn.commit()

        player_hand = [random.choice(list(cartas_emojis.keys())), random.choice(list(cartas_emojis.keys()))]
        dealer_hand = [random.choice(list(cartas_emojis.keys())), random.choice(list(cartas_emojis.keys()))]

        user_avatar_url = interaction.user.avatar.url if interaction.user.avatar else 'https://media.discordapp.net/attachments/1252053297393700885/1280946642517753876/Sin_avatar_1.png?ex=66f05786&is=66ef0606&hm=f7786f080e0b189c05ced534b0f2037b71a1d87351a643b25c360a81f8676f8b&=&format=webp&quality=lossless&width=577&height=577'
        user_name = interaction.user.display_name

        embed = discord.Embed(
            title="Blackjack  <:HermyBJ:1286141671448510475>",
            color=0x00FF00
        )
        embed.set_footer(text=user_name, icon_url=user_avatar_url)

        separador = '\u200b' * 1

        player_hand_str = f"{' '.join(cartas_emojis[card] for card in player_hand)}"
        dealer_hand_str = f"{' '.join([cartas_emojis[dealer_hand[0]], '<:Hermydeck:1286439949608161373>'])}"

        embed.add_field(
            name="*Tu mano:*",
            value=f"{player_hand_str}\n**Total:** ┋{calculate_hand_value(player_hand)}┋",
            inline=True
        )
        embed.add_field(
            name=separador,
            value=separador,
            inline=True
        )
        embed.add_field(
            name="*Mano del dealer:*",
            value=f"{dealer_hand_str}\n**Total:** ┋?┋",
            inline=True
        )
        embed.add_field(
            name="*Apuesta:*",
            value=f"{cantidad} <:Galeones:1276365877494677556>",
            inline=False
        )

        hit_button = discord.ui.Button(label="Pedir carta", style=discord.ButtonStyle.green, emoji='♣️')
        stand_button = discord.ui.Button(label="Plantarse", style=discord.ButtonStyle.red, emoji='♠️')
        help_button = discord.ui.Button(label="Ayuda", style=discord.ButtonStyle.blurple, emoji='📜')

        view = discord.ui.View()
        view.add_item(hit_button)
        view.add_item(stand_button)
        view.add_item(help_button)

        # Verificar si el jugador tiene Blackjack
        player_value = calculate_hand_value(player_hand)
        if player_value == 21 and len(player_hand) == 2:
            ganancias = int(cantidad * 2.5)
            await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (ganancias, guild_id, user_id))
            await conn.commit()

            embed.color = 0xFFD700
            embed.add_field(
                name="Resultado:",
                value=f"**¡Blackjack!** Has ganado {ganancias} <:Galeones:1276365877494677556> con un Blackjack.",
                inline=False
            )
            view.clear_items()

            await interaction.response.send_message(embed=embed, view=view)
            await conn.close()
            return

        message = await interaction.response.send_message(embed=embed, view=view)

        async def hit_callback(interaction):
            if interaction.user.id != interaction.user.id:
                return await interaction.response.send_message("No puedes interactuar con este juego.", ephemeral=True)

            new_card = random.choice(list(cartas_emojis.keys()))
            player_hand.append(new_card)

            player_value = calculate_hand_value(player_hand)

            embed.set_field_at(0, name="*Tu mano:*", value=f"{' '.join(cartas_emojis[card] for card in player_hand)}\n*Total:* ┋{player_value}┋", inline=True)

            if player_value > 21:
                embed.color = 0xFF0000
                embed.add_field(name="Resultado:", value="Te has pasado de 21 y has perdido.", inline=False)
                view.clear_items()
                await interaction.response.edit_message(embed=embed, view=view)
                await conn.close()
                return

            await interaction.response.edit_message(embed=embed, view=view)

        async def stand_callback(interaction):
            # Obtiene una nueva conexión para el callback
            conn = await get_db_connection()
            async with conn.cursor() as c:
                if interaction.user.id != interaction.user.id:
                    return await interaction.response.send_message("No puedes interactuar con este juego.", ephemeral=True)

                dealer_hand_revealed = dealer_hand[:]
                while calculate_hand_value(dealer_hand_revealed) < 17:
                    dealer_hand_revealed.append(random.choice(list(cartas_emojis.keys())))

                player_value = calculate_hand_value(player_hand)
                dealer_value = calculate_hand_value(dealer_hand_revealed)

                embed.set_field_at(2, name="*Mano del dealer:*", value=f"{' '.join(cartas_emojis[card] for card in dealer_hand_revealed)}\n*Total:* ┋{dealer_value}┋", inline=True)

                result_text = ""
                if dealer_value > 21 or player_value > dealer_value:
                    ganancias = cantidad * 2
                    await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (ganancias, guild_id, user_id))
                    await conn.commit()
                    result_text = f"**¡Ganaste!** Has ganado {ganancias} <:Galeones:1276365877494677556>."
                elif dealer_value == player_value:
                    result_text = "**¡Es un empate!** No ganaste ni perdiste."
                else:
                    result_text = "**¡Perdiste!**"

                embed.color = 0x00FF00 if "¡Ganaste!" in result_text else 0xFF0000
                embed.add_field(name="Resultado:", value=result_text, inline=False)
                view.clear_items()

                await interaction.response.edit_message(embed=embed, view=view)

    async def help_callback(interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="📜 Reglas del Blackjack:",
                description=(
                    "1. El objetivo del juego es tener una mano con un valor total más cercano a 21 sin pasarse.\n"
                    "2. Las cartas del 2 al 10 valen su valor nominal: {cartas_emojis['2']} vale 2, {cartas_emojis['9']} vale 9, etc.\n"
                    "3. Las cartas J ({cartas_emojis['J']}) , Q ({cartas_emojis['Q']}) y K ({cartas_emojis['K']}) valen 10 puntos.\n"
                    "4. El As ({cartas_emojis['A']}) puede valer 11 o 1 punto, dependiendo de lo que sea más favorable.\n"
                    "5. Si sumas más de 21 puntos, pierdes.\n"
                    "6. El dealer debe plantarse al alcanzar 17 puntos o más.\n"
                ),
                color=0x8A2BE2
            ),
            ephemeral=True
        )

    hit_button.callback = hit_callback
    stand_button.callback = stand_callback
    help_button.callback = help_callback

def close_db():
    conn.close()

def create_error_embed(ctx, message):
    embed = discord.Embed(
        title="Error",
        description=message,
        color=0xFF0000  # Rojo
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else 'https://media.discordapp.net/attachments/1252053297393700885/1280946642517753876/Sin_avatar_1.png?ex=66f05786&is=66ef0606&hm=f7786f080e0b189c05ced534b0f2037b71a1d87351a643b25c360a81f8676f8b&=&format=webp&quality=lossless&width=577&height=577')
    return embed


def calculate_hand_value(hand):
    value = sum(11 if card == 'A' else 10 if card in ['J', 'Q', 'K'] else int(card) for card in hand)
    aces = hand.count('A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


@bot.command(name='blackjack', aliases=['bj'])
async def blackjack(ctx, cantidad: str):
    guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)

    conn = await get_db_connection()
    if conn is None:
        return await ctx.send(embed=create_error_embed(ctx, "No se pudo conectar a la base de datos."))

    async with conn.cursor() as c:
   
        await c.execute("SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        result = await c.fetchone()

        if result is None:
          
            await c.execute("INSERT INTO economy (guild_id, user_id, coins, bank) VALUES (%s, %s, %s, %s)", (guild_id, user_id, 0, 0))
            await conn.commit()
            user_coins = 0
        else:
            user_coins = result[0]

        if not cantidad:
            return await ctx.send(embed=create_error_embed(ctx, "Por favor, proporciona la cantidad a apostar."))
    
        if cantidad.lower() == 'all':
            if user_coins <= 0:
                return await ctx.send(embed=create_error_embed(ctx, "No tienes suficiente efectivo para apostar toda tu cantidad."))
            cantidad = user_coins
        else:
            try:
                cantidad = int(cantidad)
            except ValueError:
                return await ctx.send(embed=create_error_embed(ctx, "La cantidad especificada no es válida."))

        if cantidad <= 0:
            return await ctx.send(embed=create_error_embed(ctx, "La cantidad a apostar debe ser mayor que cero."))

        if cantidad > user_coins:
            return await ctx.send(embed=create_error_embed(ctx, "No tienes suficientes Galeones."))

       
        await c.execute("UPDATE economy SET coins = coins - %s WHERE guild_id = %s AND user_id = %s", (cantidad, guild_id, user_id))
        await conn.commit()

        player_hand = [random.choice(list(cartas_emojis.keys())), random.choice(list(cartas_emojis.keys()))]
        dealer_hand = [random.choice(list(cartas_emojis.keys())), random.choice(list(cartas_emojis.keys()))]

        user_avatar_url = ctx.author.avatar.url if ctx.author.avatar else 'https://media.discordapp.net/attachments/1252053297393700885/1280946642517753876/Sin_avatar_1.png?ex=66f05786&is=66ef0606&hm=f7786f080e0b189c05ced534b0f2037b71a1d87351a643b25c360a81f8676f8b&=&format=webp&quality=lossless&width=577&height=577'
        user_name = ctx.author.display_name

        embed = discord.Embed(
            title="Blackjack  <:HermyBJ:1286141671448510475>",
            color=0x00FF00
        )
        embed.set_footer(text=user_name, icon_url=user_avatar_url)

        separador = '\u200b' * 1

        player_hand_str = f"{' '.join(cartas_emojis[card] for card in player_hand)}"
        dealer_hand_str = f"{' '.join([cartas_emojis[dealer_hand[0]], '<:Hermydeck:1286439949608161373>'])}"

        embed.add_field(
            name="*Tu mano:*",
            value=f"{player_hand_str}\n**Total:** ┋{calculate_hand_value(player_hand)}┋",
            inline=True
        )
        embed.add_field(
            name=separador,
            value=separador,
            inline=True
        )
        embed.add_field(
            name="*Mano del dealer:*",
            value=f"{dealer_hand_str}\n**Total:** ┋?┋",
            inline=True
        )
        embed.add_field(
            name="*Apuesta:*",
            value=f"{cantidad} <:Galeones:1276365877494677556>",
            inline=False
        )

        hit_button = discord.ui.Button(label="Pedir carta", style=discord.ButtonStyle.green, emoji='♣️')
        stand_button = discord.ui.Button(label="Plantarse", style=discord.ButtonStyle.red, emoji='♠️')
        double_down_button = discord.ui.Button(label="Doblar", style=discord.ButtonStyle.blurple, emoji='📜')
        # split_button = discord.ui.Button(label="Dividir", style=discord.ButtonStyle.blurple, emoji='📜')
        help_button = discord.ui.Button(label="Ayuda", style=discord.ButtonStyle.blurple, emoji='📜')
        
        # if player_hand[0] == player_hand[1]:
        #     split_button.disabled = False
        # else:
        #     split_button.disabled = True

        view = discord.ui.View()
        view.add_item(hit_button)
        view.add_item(stand_button)
        view.add_item(double_down_button)
        # view.add_item(split_button)
        view.add_item(help_button)

       
        player_value = calculate_hand_value(player_hand)
        if player_value == 21 and len(player_hand) == 2:
            ganancias = int(cantidad * 2.5)
            await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (ganancias, guild_id, user_id))
            await conn.commit()

            embed.color = 0xFFD700
            embed.add_field(
                name="Resultado:",
                value=f"**¡Blackjack!** Has ganado {ganancias} <:Galeones:1276365877494677556> con un Blackjack.",
                inline=False
            )
            view.clear_items()

            await ctx.send(embed=embed, view=view)
            await conn.close()
            return

        message = await ctx.send(embed=embed, view=view)

        async def hit_callback(interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=create_error_embed(ctx, "No puedes interactuar con este juego."), ephemeral=True)

            new_card = random.choice(list(cartas_emojis.keys()))
            player_hand.append(new_card)

            player_value = calculate_hand_value(player_hand)

            embed.set_field_at(0, name="*Tu mano:*", value=f"{' '.join(cartas_emojis[card] for card in player_hand)}\n*Total:* ┋{player_value}┋", inline=True)

            if player_value > 21:
                embed.color = 0xFF0000
                embed.add_field(name="Resultado:", value="Te has pasado de 21 y has perdido.", inline=False)
                view.clear_items()
                await interaction.response.edit_message(embed=embed, view=view)
                await conn.close()
                return

            await interaction.response.edit_message(embed=embed, view=view)

        async def stand_callback(interaction):
            conn = await get_db_connection()
            if conn is None:
                return await interaction.response.send_message(embed=create_error_embed(ctx, "No se pudo conectar a la base de datos."), ephemeral=True)

            async with conn.cursor() as c:
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message(embed=create_error_embed(ctx, "No puedes interactuar con este juego."), ephemeral=True)

                dealer_hand_revealed = dealer_hand[:]
                while calculate_hand_value(dealer_hand_revealed) < 17:
                    dealer_hand_revealed.append(random.choice(list(cartas_emojis.keys())))

                player_value = calculate_hand_value(player_hand)
                dealer_value = calculate_hand_value(dealer_hand_revealed)

                embed.set_field_at(2, name="*Mano del dealer:*", value=f"{' '.join(cartas_emojis[card] for card in dealer_hand_revealed)}\n*Total:* ┋{dealer_value}┋", inline=True)

                result_text = ""
                if dealer_value > 21 or player_value > dealer_value:
                    ganancias = cantidad * 2
                    await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (ganancias, guild_id, user_id))
                    await conn.commit()
                    result_text = f"**¡Ganaste!** Has ganado {ganancias} <:Galeones:1276365877494677556>."
                    embed.color = 0x00FF00 #verde

                elif player_value < dealer_value:
                    result_text = "El dealer gana. Pierdes la partida."
                    embed.color = 0xFF0000  #rojo

                else:
                    await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (cantidad, guild_id, user_id))
                    await conn.commit()
                    result_text = "Es un empate. Recuperas tu apuesta."
                    embed.color = 0x808080  #gris

                embed.add_field(name="Resultado:", value=result_text, inline=False)
                view.clear_items()

                await interaction.response.edit_message(embed=embed, view=view)
                await conn.close()


        # Doblar Apuesta - Genaa
        async def double_down_callback(interaction, cantidad, user_coins):

            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=create_error_embed(ctx, "No puedes interactuar con este juego."), ephemeral=True)
            
            if cantidad * 2 > user_coins:
                return await interaction.response.send_message(embed=create_error_embed(ctx, "Nesecitas mas monedas para doblar la apuesta."), ephemeral=True)

            cantidad *= 2

            new_card = random.choice(list(cartas_emojis.keys()))
            player_hand.append(new_card)
            player_value = calculate_hand_value(player_hand)

            embed.set_field_at(0, name="*Tu mano:*", value=f"{' '.join(cartas_emojis[card] for card in player_hand)}\n*Total:* ┋{player_value}┋", inline=True)

            if player_value > 21:
                embed.add_field(name="Resultado:", value="Te has pasado de 21 y has perdido.", inline=False)
                view.clear_items()
                await interaction.response.edit_message(embed=embed, view=view)
                await conn.close()
                return
            
            dealer_hand_revelead = dealer_hand[:]
            while calculate_hand_value(dealer_hand_revelead) < 17:
                dealer_hand_revelead.append(random.choice(list(cartas_emojis.keys())))
            
            dealer_value = calculate_hand_value(dealer_hand_revelead)
            
            embed.set_field_at(2, name="*Mano del dealer:*", value=f"{' '.join(cartas_emojis[card] for card in dealer_hand_revelead)}\n*Total:* ┋{dealer_value}┋", inline=True)

            if dealer_value > 21 or player_value > dealer_value:
                ganancias = cantidad * 2
                await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (ganancias, guild_id, user_id))
                await conn.commit()
                result_text = f"**¡Ganaste!** Has ganado {ganancias} <:Galeones:1276365877494677556>."
                embed.color = 0x00FF00 
            elif player_value < dealer_value:
                result_text = f"El dealer gana. Pierdes la partida."
                embed.color = 0xFF0000
            elif player_value > 21:
                result_text = "Perdiste, te pasaste de 21."
                view.clear_items()
                embed.color = 0xFF0000
            else:
                await c.execute("UPDATE economy SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (cantidad, guild_id, user_id))
                await conn.commit()
                result_text = "Es un empate. Recuperas tu apuesta."
                embed.color = 0x808080

            embed.add_field(name="Resultado:", value=result_text, inline=False)
            view.clear_items()
            await interaction.response.edit_message(embed=embed, view=view)
            await conn.close()


        async def help_callback(interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=create_error_embed(ctx, "No puedes interactuar con este juego."), ephemeral=True)

            try:
                await interaction.user.send(
                    embed=discord.Embed(
                        title="Blackjack",
                        description="1. El objetivo principal del juego es conseguir una mano cuyo valor total se acerque lo más posible a 21 sin excederse. Alcanzar exactamente 21 es el mejor resultado, así que ¡ten cuidado con cada carta que elijas!\n"

"2. Las cartas numeradas del 2 al 10 tienen un valor equivalente a su número. Por ejemplo, la carta <:HermyBJ2:1286126194516824087> vale 2 puntos, la carta <:HermyBJ3:1286124903698796627> vale 3 puntos, y así sucesivamente hasta la carta <:HermyBJ10:1286127112079544411> que vale 10 puntos. Cada número cuenta, así que usa las cartas sabiamente para sumar tu total.\n"

"3. Las cartas de la corte, J (<:HermyBJJ:1286127302878433341>), Q (<:HermyBJQ:1286124763932135467>) y K (<:HermyBJK:1286127496894615563>), valen cada una 10 puntos. Estas cartas pueden ser clave para acercarte a 21, así que no las subestimes en tu estrategia.\n"

"4. El As (<:HermyBJA:1286125257039675423>) es una carta especial que puede valer 11 o 1 punto, según lo que te beneficie más. Si tu mano ya tiene un alto valor, puede ser mejor contar el As como 1 punto para evitar pasarte de 21. Este aspecto flexible del As puede ser crucial para ganar, así que evalúa bien tus opciones.\n"

"5. Si tu mano suma más de 21 puntos, perderás automáticamente la ronda, así que mantente alerta y maneja tus cartas con cuidado. Recuerda que el objetivo es acercarte a 21, no sobrepasarlo.\n"

"6. El dealer tiene reglas específicas: debe plantarse (no pedir más cartas) cuando su mano alcance 17 puntos o más. Esto significa que debes ser estratégico en tu juego, ya que debes superar al dealer sin sobrepasar el 21. A veces, una jugada audaz puede llevarte a la victoria, pero ten cuidado de no ser demasiado arriesgado.\n"

"7. Recuerda siempre que el juego no solo se basa en la suerte, sino también en la estrategia. Observa las cartas que han salido y calcula tus posibilidades. Una buena estrategia puede marcar la diferencia entre ganar y perder. ¡Buena suerte y que comience el juego!",
                        color=0x0000FF
                    )
                )
                help_button.disabled = True
                await interaction.response.edit_message(view=view)
            except discord.Forbidden:
                await interaction.response.send_message(embed=create_error_embed(ctx, "No puedo enviarte el mensaje de ayuda por privado. Verifica tus ajustes de privacidad."), ephemeral=True)

        hit_button.callback = hit_callback
        stand_button.callback = stand_callback
        double_down_button.callback = lambda interaction: double_down_callback(interaction, cantidad, user_coins)
        help_button.callback = help_callback

# Diccionario para almacenar los intentos por usuario y servidor (guild)
attempts = defaultdict(lambda: {"count": 0, "last_time": 0})
COOLDOWN_TIME = 300  # 5 minutos en segundos
MAX_ATTEMPTS = 5

@bot.command(name='slots')
async def slots(ctx, amount: str = None):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    current_time = time.time()

    # Verificar intentos y cooldown
    user_attempts = attempts[(guild_id, user_id)]
    if current_time - user_attempts["last_time"] >= COOLDOWN_TIME:
        user_attempts["count"] = 0  # Reinicia el conteo de intentos si el cooldown ha expirado

    if user_attempts["count"] >= MAX_ATTEMPTS:
        time_left = COOLDOWN_TIME - (current_time - user_attempts["last_time"])
        minutes, seconds = divmod(int(time_left), 60)
        
        # Crear embed rojo de advertencia
        warning_embed = discord.Embed(
            title="⚠️ Límite de intentos alcanzado",
            description=f"has alcanzado el límite de 5 intentos. Intenta nuevamente en {minutes}m {seconds}s.",
            color=0xFF0000
        )
        warning_embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url if ctx.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
        
        await ctx.send(embed=warning_embed)
        return

    # Incrementar el contador de intentos
    user_attempts["count"] += 1
    user_attempts["last_time"] = current_time

    # Obtener saldo de coins del usuario
    async def get_user_coins(guild_id, user_id):
        conn = await get_db_connection()
        try:
            async with conn.cursor() as c:
                await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
                result = await c.fetchone()
                return result[0] if result else 0
        finally:
            conn.close()

    # Actualizar saldo de coins del usuario
    async def update_user_coins(guild_id, user_id, coins):
        conn = await get_db_connection()
        try:
            async with conn.cursor() as c:
                await c.execute(
                    'UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s',
                    (max(coins, 0), guild_id, user_id)
                )
                await conn.commit()
        finally:
            conn.close()

    user_coins = await get_user_coins(guild_id, user_id)

    # Obtener avatar del usuario
    def get_avatar_url(user):
        return user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

    # Enviar mensaje de embed con avatar del usuario
    async def send_embed_with_author(ctx, title, description, color):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_author(name=ctx.author.name, icon_url=get_avatar_url(ctx.author))
        await ctx.send(embed=embed)

    # Validación de cantidad de apuesta
    if not amount:
        await send_embed_with_author(ctx, "<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "Debes ingresar la cantidad que deseas apostar.", color=0xFF0000)
        return                    

    # Procesar la apuesta
    if amount.lower() == 'all':
        if user_coins == 0:
            await send_embed_with_author(ctx, "<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "No tienes Galeones en efectivo para apostar.", color=0xFF0000)
            return
        amount = user_coins
    else:
        try:
            amount = int(amount)
        except ValueError:
            await send_embed_with_author(ctx, "<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "Por favor, ingresa una cantidad válida o 'all' para apostar todo tu efectivo.", color=0xFF0000)
            return

    # Verificación de saldo insuficiente o apuestas negativas
    if amount > user_coins:
        await send_embed_with_author(ctx, "<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "No tienes suficientes Galeones en efectivo.", color=0xFF0000)
        return
    elif amount <= 0:
        await send_embed_with_author(ctx, "<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "No puedes apostar una cantidad negativa o cero.", color=0xFF0000)
        return

    # Actualizar saldo después de la apuesta
    user_coins -= amount
    await update_user_coins(guild_id, user_id, user_coins)

    # Generar resultados de slots
    slots = [':compression:', ':firecracker:', ':tools:']
    result_top = [random.choice(slots) for _ in range(3)]
    result_middle = [random.choice(slots) for _ in range(3)]
    result_bottom = [random.choice(slots) for _ in range(3)]

    # Formatear mensaje de los resultados
    def get_slot_message():
        return (
            f"{result_top[0]} | {result_top[1]} | {result_top[2]}\n"
            f"{result_middle[0]} | {result_middle[1]} | {result_middle[2]} ⬅\n"
            f"{result_bottom[0]} | {result_bottom[1]} | {result_bottom[2]}"
        )

    # Verificar si hay tres símbolos iguales en la fila del medio
    if result_middle[0] == result_middle[1] == result_middle[2]:
        winnings_multiplier = random.randint(4, 10)
        winnings = amount * winnings_multiplier
        user_coins += winnings
        await update_user_coins(guild_id, user_id, user_coins)

        embed = discord.Embed(
            title="🎉 ¡Ganaste!",
            description=get_slot_message(),
            color=0x00FF00
        )
        embed.add_field(name="Premio", value=f"¡Felicidades {ctx.author.mention}! Ganaste {format_number(winnings)} <:Galeones:1276365877494677556>!", inline=False)
        embed.add_field(name="Apuesta", value=f"Has apostado {format_number(amount)} <:Galeones:1276365877494677556>.", inline=False)
    else:
        embed = discord.Embed(
            title="<:Wlingslots:1279332993764163634> Perdiste\n\n¡Suerte la próxima!",
            description=get_slot_message(),
            color=0xFF0000
        )
        embed.add_field(name="Pérdida", value=f"Has perdido {format_number(amount)} <:Galeones:1276365877494677556>.", inline=False)

    embed.set_author(name=ctx.author.name, icon_url=get_avatar_url(ctx.author))
    await ctx.send(embed=embed)

# Formato de números
def format_number(number):
    return "{:,}".format(number)

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def slots_command(self, interaction: discord.Interaction, amount: str):
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        current_time = time.time()

        # Verificar intentos y cooldown
        user_attempts = attempts[(guild_id, user_id)]
        if current_time - user_attempts["last_time"] >= COOLDOWN_TIME:
            user_attempts["count"] = 0  # Reinicia el conteo de intentos si el cooldown ha expirado

        if user_attempts["count"] >= MAX_ATTEMPTS:
            time_left = COOLDOWN_TIME - (current_time - user_attempts["last_time"])
            minutes, seconds = divmod(int(time_left), 60)
            
            # Crear embed rojo de advertencia
            warning_embed = discord.Embed(
                title="⚠️ Límite de intentos alcanzado",
                description=f"Has alcanzado el límite de 5 intentos. Intenta nuevamente en {minutes}m {seconds}s.",
                color=0xFF0000
            )
            warning_embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
            
            await interaction.response.send_message(embed=warning_embed, ephemeral=True)
            return

        # Incrementar el contador de intentos
        user_attempts["count"] += 1
        user_attempts["last_time"] = current_time

        # Obtener saldo de coins del usuario
        async def get_user_coins(guild_id, user_id):
            conn = await get_db_connection()
            try:
                async with conn.cursor() as c:
                    await c.execute('SELECT coins FROM economy WHERE guild_id = %s AND user_id = %s', (guild_id, user_id))
                    result = await c.fetchone()
                    return result[0] if result else 0
            finally:
                conn.close()

        # Actualizar saldo de coins del usuario
        async def update_user_coins(guild_id, user_id, coins):
            conn = await get_db_connection()
            try:
                async with conn.cursor() as c:
                    await c.execute(
                        'UPDATE economy SET coins = %s WHERE guild_id = %s AND user_id = %s',
                        (max(coins, 0), guild_id, user_id)
                    )
                    await conn.commit()
            finally:
                conn.close()

        user_coins = await get_user_coins(guild_id, user_id)

        # Obtener avatar del usuario
        def get_avatar_url(user):
            return user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

        # Enviar mensaje de embed con avatar del usuario
        async def send_embed_with_author(title, description, color):
            embed = discord.Embed(title=title, description=description, color=color)
            embed.set_author(name=interaction.user.name, icon_url=get_avatar_url(interaction.user))
            await interaction.response.send_message(embed=embed)

        # Procesar la apuesta
        if amount.lower() == 'all':
            if user_coins == 0:
                await send_embed_with_author("<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "No tienes Galeones en efectivo para apostar.", color=0xFF0000)
                return
            amount = user_coins
        else:
            try:
                amount = int(amount)
            except ValueError:
                await send_embed_with_author("<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "Por favor, ingresa una cantidad válida o 'all' para apostar todo tu efectivo.", color=0xFF0000)
                return

        # Verificación de saldo insuficiente o apuestas negativas
        if amount > user_coins:
            await send_embed_with_author("<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "No tienes suficientes Galeones en efectivo.", color=0xFF0000)
            return
        elif amount <= 0:
            await send_embed_with_author("<:Gringotts_Bank:1276368414528503858> Notificación del **Casino Mágico**", "No puedes apostar una cantidad negativa o cero.", color=0xFF0000)
            return

        # Actualizar saldo después de la apuesta
        user_coins -= amount
        await update_user_coins(guild_id, user_id, user_coins)

        # Generar resultados de slots
        slots = [':compression:', ':firecracker:', ':tools:']
        result_top = [random.choice(slots) for _ in range(3)]
        result_middle = [random.choice(slots) for _ in range(3)]
        result_bottom = [random.choice(slots) for _ in range(3)]

        # Formatear mensaje de los resultados
        def get_slot_message():
            return (
                f"{result_top[0]} | {result_top[1]} | {result_top[2]}\n"
                f"{result_middle[0]} | {result_middle[1]} | {result_middle[2]} ⬅\n"
                f"{result_bottom[0]} | {result_bottom[1]} | {result_bottom[2]}"
            )

        # Verificar si hay tres símbolos iguales en la fila del medio
        if result_middle[0] == result_middle[1] == result_middle[2]:
            winnings_multiplier = random.randint(4, 10)
            winnings = amount * winnings_multiplier
            user_coins += winnings
            await update_user_coins(guild_id, user_id, user_coins)

            embed = discord.Embed(
                title="🎉 ¡Ganaste!",
                description=get_slot_message(),
                color=0x00FF00
            )
            embed.add_field(name="Premio", value=f"¡Felicidades {interaction.user.mention}! Ganaste {format_number(winnings)} <:Galeones:1276365877494677556>!", inline=False)
            embed.add_field(name="Apuesta", value=f"Has apostado {format_number(amount)} <:Galeones:1276365877494677556>.", inline=False)
        else:
            embed = discord.Embed(
                title="<:Wlingslots:1279332993764163634> Perdiste\n\n¡Suerte la próxima!",
                description=get_slot_message(),
                color=0xFF0000
            )
            embed.add_field(name="Pérdida", value=f"Has perdido {format_number(amount)} <:Galeones:1276365877494677556>.", inline=False)

        embed.set_author(name=interaction.user.name, icon_url=get_avatar_url(interaction.user))
        await interaction.response.send_message(embed=embed)

# Formato de números
def format_number(number):
    return "{:,}".format(number)

async def setup(bot):
    casino_cog = Casino(bot)
    await bot.add_cog(casino_cog)

    @bot.tree.command(name="slots", description="Juega en el Casino Mágico y apuesta tus Galeones.")
    async def slots(interaction: discord.Interaction, amount: str):
        await casino_cog.slots_command(interaction, amount)
    
# Diccionario para rastrear partidas activas por usuario
active_games = {}

# Función auxiliar para quitar tildes de una palabra
def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

@bot.command(name='profile')
async def profile(ctx, user: discord.User = None):
    user = user or ctx.author
    guild_id = str(ctx.guild.id)
    user_id = str(user.id)

    conn = await get_db_connection()
    async with conn.cursor() as c:
        # ECONOMY DATA
        await c.execute(
            "SELECT coins, bank FROM economy WHERE guild_id = %s AND user_id = %s",
            (guild_id, user_id)
        )
        result = await c.fetchone()
        coins, bank = (result if result else (0, 0))

        # PROFILE DATA
        await c.execute(
            "SELECT created_at, work_count FROM profile WHERE guild_id = %s AND user_id = %s",
            (guild_id, user_id)
        )
        profile_data = await c.fetchone()
        if profile_data:
            created_at, work_count = profile_data
        else:
            created_at = int(datetime.datetime.utcnow().timestamp())
            work_count = 0
            await c.execute(
                "INSERT INTO profile (guild_id, user_id, created_at, work_count) VALUES (%s, %s, %s, %s)",
                (guild_id, user_id, created_at, work_count)
            )
            await conn.commit()
    conn.close()

    # Formateo de datos
    total = coins + bank
    total_fmt = f"{total:,}".replace(",", ".")
    coins_fmt = f"{coins:,}".replace(",", ".")
    bank_fmt = f"{bank:,}".replace(",", ".")
    created_dt = f"Registrado el: <t:{created_at}:F> (<t:{created_at}:R>)"

    # Logros
    milestones = [1, 100, 300, 600, 1000, 1500, 2500, 3000]
    emojis = ['🥚', '🐭', '🐸', '🦔', '🦉', '🦄', '🐉', '👑']
    achievements = "".join(emojis[i] for i, m in enumerate(milestones) if work_count >= m) or "Sin logros aún."

    # Embed del perfil
    embed = discord.Embed(title=f"🔮 Perfil de {user.name}", color=0x8A2BE2)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.add_field(name="💰 Cash", value=f"`{coins_fmt}` <:Galeones:1276365877494677556>", inline=True)
    embed.add_field(name="🏦 Banco", value=f"`{bank_fmt}` <:Galeones:1276365877494677556>", inline=True)
    embed.add_field(name="📊 Total", value=f"`{total_fmt}` <:Galeones:1276365877494677556>", inline=True)
    embed.add_field(name="📅 Registro", value=created_dt, inline=False)
    embed.add_field(name="🛠️ Trabajos realizados", value=f"`{work_count}`", inline=True)
    embed.add_field(name="🏆 Logros", value=achievements, inline=True)

    # Vista con botón para varita
    class WandView(discord.ui.View):
        def __init__(self, user_id, guild_id):
            super().__init__()
            self.user_id = user_id
            self.guild_id = guild_id

        @discord.ui.button(label="Ver Varita", style=discord.ButtonStyle.primary, emoji="🪄")
        async def show_wand(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != int(self.user_id):
                await interaction.response.send_message(
                    "⛔ Solo el dueño del perfil puede ver esta varita.", ephemeral=True)
                return

            conn = await get_db_connection()
            async with conn.cursor() as c:
                await c.execute(
                    "SELECT wood, core, length, flexibility, durability FROM wands WHERE guild_id = %s AND user_id = %s",
                    (self.guild_id, self.user_id)
                )
                wand_data = await c.fetchone()
            conn.close()

            if wand_data:
                wood, core, length, flexibility, durability = wand_data
                wand_embed = discord.Embed(title="🪄 Información de la Varita", color=0xFFD700)
                wand_embed.add_field(name="🌳 Madera", value=wood or "Desconocido", inline=True)
                wand_embed.add_field(name="💠 Núcleo", value=core or "Desconocido", inline=True)
                wand_embed.add_field(name="📏 Longitud", value=f"{length or 'Desconocida'} pulgadas", inline=True)
                wand_embed.add_field(name="🌀 Flexibilidad", value=flexibility or "Desconocida", inline=True)
                wand_embed.add_field(name="🛡️ Durabilidad", value=f"{durability}/10", inline=True)
                await interaction.response.send_message(embed=wand_embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "🪄 Este mago aún no tiene una varita registrada.", ephemeral=True)

    await ctx.send(embed=embed, view=WandView(user_id=user_id, guild_id=guild_id))



@bot.command()
async def loginfo(ctx, usuario_id: int):
    servidor_id = ctx.guild.id
    hoy = datetime.utcnow().date()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)

    conn = await get_db_connection()
    cursor = await conn.cursor(aiomysql.DictCursor)

    # Cantidad total
    await cursor.execute("""
        SELECT COUNT(*) AS total FROM comando_logs
        WHERE usuario_id = %s AND servidor_id = %s
    """, (usuario_id, servidor_id))
    total = (await cursor.fetchone())["total"] or 0

    async def contar_comandos(fecha_inicio, fecha_fin=None):
        if fecha_fin:
            await cursor.execute("""
                SELECT COUNT(*) AS total FROM comando_logs
                WHERE usuario_id = %s AND servidor_id = %s AND DATE(fecha) BETWEEN %s AND %s
            """, (usuario_id, servidor_id, fecha_inicio, fecha_fin))
        else:
            await cursor.execute("""
                SELECT COUNT(*) AS total FROM comando_logs
                WHERE usuario_id = %s AND servidor_id = %s AND DATE(fecha) = %s
            """, (usuario_id, servidor_id, fecha_inicio))
        return (await cursor.fetchone())["total"] or 0

    hoy_count = await contar_comandos(hoy)
    semana_count = await contar_comandos(hace_7_dias, hoy)
    mes_count = await contar_comandos(hace_30_dias, hoy)

    async def top_comandos(fecha_inicio=None):
        if fecha_inicio:
            await cursor.execute("""
                SELECT comando, COUNT(*) as cantidad FROM comando_logs
                WHERE usuario_id = %s AND servidor_id = %s AND DATE(fecha) >= %s
                GROUP BY comando ORDER BY cantidad DESC LIMIT 10
            """, (usuario_id, servidor_id, fecha_inicio))
        else:
            await cursor.execute("""
                SELECT comando, COUNT(*) as cantidad FROM comando_logs
                WHERE usuario_id = %s AND servidor_id = %s
                GROUP BY comando ORDER BY cantidad DESC LIMIT 10
            """, (usuario_id, servidor_id))
        return await cursor.fetchall()

    top_hoy = await top_comandos(hoy)
    top_semana = await top_comandos(hace_7_dias)
    top_mes = await top_comandos(hace_30_dias)
    top_total = await top_comandos()

    # Historial completo para el .txt
    await cursor.execute("""
        SELECT comando, fecha, canal_nombre FROM comando_logs
        WHERE usuario_id = %s AND servidor_id = %s
        ORDER BY fecha DESC
    """, (usuario_id, servidor_id))
    historial = await cursor.fetchall()

    await cursor.close()
    conn.close()

    user = ctx.guild.get_member(usuario_id)
    username = user.display_name if user else str(usuario_id)

    def formatear_top(lista):
        if not lista:
            return "Sin datos"
        return "\n".join(f"`{c['comando']}`: {c['cantidad']}" for c in lista)

    def porcentaje(parcial):
        return f"{(parcial / total * 100):.2f}%" if total > 0 else "0%"

    # Embed
    embed = discord.Embed(
        title=f"📊 Estadísticas de {username}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Servidor: {ctx.guild.name} | Usuario ID: {usuario_id}")

    embed.add_field(name="📅 Hoy", value=f"{hoy_count} comandos ({porcentaje(hoy_count)})", inline=False)
    embed.add_field(name="🗓️ Últimos 7 días", value=f"{semana_count} comandos ({porcentaje(semana_count)})", inline=False)
    embed.add_field(name="📆 Últimos 30 días", value=f"{mes_count} comandos ({porcentaje(mes_count)})", inline=False)
    embed.add_field(name="📚 Total histórico", value=f"{total} comandos", inline=False)

    embed.add_field(name="🔝 Top comandos hoy", value=formatear_top(top_hoy), inline=True)
    embed.add_field(name="🔝 Top últimos 7 días", value=formatear_top(top_semana), inline=True)
    embed.add_field(name="🔝 Top últimos 30 días", value=formatear_top(top_mes), inline=True)
    embed.add_field(name="🏆 Top histórico", value=formatear_top(top_total), inline=True)

    # Archivo txt
    output = io.StringIO()
    output.write(f"📄 Historial de comandos del usuario {username} en el servidor {ctx.guild.name}\n")
    output.write("Ordenado del más reciente al más antiguo\n\n")

    for log in historial:
        fecha = log["fecha"].strftime("%Y-%m-%d %H:%M:%S") if log["fecha"] else "Desconocida"
        canal = log["canal_nombre"] or "Desconocido"
        comando = log["comando"]

        if user:
            roles = [r.name for r in user.roles if r.name != "@everyone"]
            roles_str = ", ".join(roles) if roles else "Sin roles"
        else:
            roles_str = "Desconocido"

        output.write(f"[{fecha}] #{canal} | {comando} | Roles: {roles_str}\n")

    output.seek(0)
    file = discord.File(fp=output, filename=f"loginfo_{usuario_id}.txt")

    await ctx.send(embed=embed, file=file)


@bot.command()
async def ecoinfo(ctx, user_id: str):
    guild_id = str(ctx.guild.id)

    conn = await get_db_connection()
    async with conn.cursor(aiomysql.DictCursor) as cursor:

        # Obtener saldo actual
        await cursor.execute("""
            SELECT coins, bank FROM economy
            WHERE guild_id = %s AND user_id = %s
        """, (guild_id, user_id))
        economy = await cursor.fetchone()

        if not economy:
            await ctx.send("❌ Ese usuario no tiene datos registrados.")
            await conn.ensure_closed()
            return

        saldo_actual = f"💰 Coins: {economy['coins']:,}\n🏦 Bank: {economy['bank']:,}"

        # Fechas
        now = datetime.now(gmt_minus_3)
        timeframes = {
            "Hoy": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "7 días": now - timedelta(days=7),
            "30 días": now - timedelta(days=30),
            "60 días": now - timedelta(days=60)
        }

        # Calcular estadísticas
        estadisticas = {}

        for periodo, desde in timeframes.items():
            await cursor.execute("""
                SELECT cash_change, bank_change
                FROM economy_log
                WHERE guild_id = %s AND user_id = %s AND timestamp >= %s
            """, (guild_id, user_id, desde))
            rows = await cursor.fetchall()

            ganancias = {"cash": 0, "bank": 0}
            perdidas = {"cash": 0, "bank": 0}

            for row in rows:
                # CASH
                if row['cash_change'] and row['cash_change'] > 0:
                    ganancias["cash"] += row['cash_change']
                elif row['cash_change'] and row['cash_change'] < 0:
                    perdidas["cash"] += row['cash_change']

                # BANK
                if row['bank_change'] and row['bank_change'] > 0:
                    ganancias["bank"] += row['bank_change']
                elif row['bank_change'] and row['bank_change'] < 0:
                    perdidas["bank"] += row['bank_change']

            estadisticas[periodo] = {
                "ganancias": ganancias,
                "perdidas": perdidas
            }

        # Obtener historial completo para el .txt
        await cursor.execute("""
            SELECT * FROM economy_log
            WHERE guild_id = %s AND user_id = %s
            ORDER BY timestamp DESC
        """, (guild_id, user_id))
        logs = await cursor.fetchall()

        log_text = f"Historial completo de movimientos para user_id: {user_id}\n\n"
        for log in logs:
            log_text += f"[{log['timestamp']}] "
            log_text += f"ACTION: {log['action_type']} | "
            if log['cash_change']:
                log_text += f"CASH Δ: {log['cash_change']} (Old: {log['old_cash']}, New: {log['new_cash']}) | "
            if log['bank_change']:
                log_text += f"BANK Δ: {log['bank_change']} (Old: {log['old_bank']}, New: {log['new_bank']}) | "
            if log['channel_id']:
                log_text += f"Channel: {log['channel_id']}"
            log_text += "\n"

        # Crear archivo .txt
        file = discord.File(io.StringIO(log_text), filename=f"economy_log_{user_id}.txt")

        # Crear embed
        embed = discord.Embed(
            title=f"📈 Estadísticas económicas de <@{user_id}>",
            description=saldo_actual,
            color=discord.Color.gold()
        )

        for periodo, data in estadisticas.items():
            embed.add_field(
                name=f"📊 {periodo} - Ganancias",
                value=f"💰 Coins: `{data['ganancias']['cash']}`\n🏦 Bank: `{data['ganancias']['bank']}`",
                inline=False
            )
            embed.add_field(
                name=f"📉 {periodo} - Pérdidas",
                value=f"💰 Coins: `{abs(data['perdidas']['cash'])}`\n🏦 Bank: `{abs(data['perdidas']['bank'])}`",
                inline=False
            )

        await ctx.send(embed=embed, file=file)

    conn.close()

active_games = {}

@bot.command()
async def syc(ctx):
    try:
        # Sincroniza todos los comandos slash
        synced = await bot.tree.sync()
        await ctx.send(f"`Comandos sincronizados correctamente: {len(synced)} comandos.`")
    except Exception as e:
        await ctx.send(f"Error al sincronizar comandos: {e}")

#Run 
bot.run(token)




