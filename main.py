import discord
import random
import asyncio
import sqlite3
import datetime
import pytz
import os

from discord.ext import commands
from keep_alive import keep_alive
from discord.ext.commands import MissingPermissions, CommandNotFound

bot_secret = os.environ['bot_pass']
database = "database.db"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Excluir tabela de aniversários
#c.execute("DROP TABLE IF EXISTS birthdays")

c.execute('''CREATE TABLE IF NOT EXISTS birthdays
             (user_id INTEGER PRIMARY KEY, birthday TEXT, last_sent TEXT, sent_notification INTEGER DEFAULT 0)''')

conn.commit()
conn.close()

bot.sortition_active = False

@bot.event
async def on_member_join(member):
    print(f'{member.name} has joined the server')
    channel = bot.get_channel(951831987549798410)
    print(channel)
    await channel.send(f"```\n{member.name} has joined the server\n```")

@bot.event
async def on_member_remove(member):
    print(f'{member.name} has left the server')
    channel = bot.get_channel(1024414658674835506)
    print(channel)
    await channel.send(f"```\n{member.name} has left the server\n```")

@bot.command()
async def sort(ctx):
    if ctx.message.author.guild_permissions.administrator:
        if not bot.sortition_active:
            bot.sortition_active = True
            msg = await ctx.send("Enter password to perform sortition:")

            def check(m):
                return m.author == ctx.message.author and m.channel == ctx.channel

            password = await bot.wait_for('message', check=check)
            await password.delete()

            if password.content == bot_secret:
                users = [member for member in ctx.guild.members if not member.bot]
                if len(users) > 0:
                    winner = random.choice(users)
                    await msg.delete()
                    await ctx.send(f"```\nThe Winner Is: {winner}!\n```")
                else:
                    await msg.delete()
                    await ctx.send("No eligible members found in the server.")
            else:
                await msg.delete()
                await ctx.send("Incorrect password, try again:")

            bot.sortition_active = False
        else:
            await ctx.send("There's already a sortition in progress. Please wait until it's finished.")
    else:
        await ctx.send("```\nYou don't have permission to perform sortition :(\n```")

@bot.command()
@commands.has_permissions(administrator=True)
@commands.has_permissions(manage_messages=True)
async def clear(ctx):
    await ctx.send("Clearing all messages...")
    async for message in ctx.channel.history(limit=None):
        await message.delete()
        await asyncio.sleep(1)
    await ctx.send("All messages cleared!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send("```\nThis command does not exist!\n```")
    elif isinstance(error, MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        help_error = f"Error: {error}"
        await ctx.send(f"```\n{help_error}\n```")
     
@bot.command()
async def links(ctx):
    help_command = """
    
Server Invite:
[https://discord.gg/wXqcJDHht8]
    
Telegram:
[https://t.me/+4KfOA1ewYrI1ZWFh]

Site:
[https://noclipstudio.net]

Mail:
[**noclipstudio@null.net**]"""
  
    await ctx.send(help_command)

    await ctx.send(f"```\n{help_command}\n```")

@bot.command()
async def birthday(ctx):
    await ctx.send("Please enter your birthday in DD/MM/YYYY format:")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        birthday = msg.content

        if len(birthday) == 10 and birthday[2] == "/" and birthday[5] == "/":
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM birthdays WHERE user_id = ?", (ctx.author.id,))
            existing_data = c.fetchone()

            if existing_data:
                await ctx.send("You have already registered your birthday before.")
            else:
                try:
                    date_obj = datetime.strptime(birthday, '%d/%m/%Y').date()
                    formatted_birthday = date_obj.strftime("%Y-%m-%d")
                    c.execute("INSERT INTO birthdays (user_id, birthday, last_sent) VALUES (?, ?, NULL)",
                              (ctx.author.id, formatted_birthday))
                    conn.commit()
                    await ctx.send("Your birthday has been successfully recorded!")
                except ValueError:
                    await ctx.send("Invalid date format. Please try again.")

            conn.close()
        else:
            await ctx.send("Invalid date format. Please try again.")

    except asyncio.TimeoutError:
        await ctx.send("Time is over. Please try again later.")

    today = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%m-%d")
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM birthdays WHERE strftime('%m-%d', birthday) = ?", (today,))
    users = c.fetchall()

    channel_id = 951799663185522718
    channel = bot.get_channel(channel_id)
    print(f"Target channel: {channel}")

    if channel:
        for user in users:
            member = channel.guild.get_member(user[0])
            if member:
                c.execute("SELECT last_sent FROM birthdays WHERE user_id = ?", (user[0],))
                last_sent = c.fetchone()[0]
                if last_sent is None or last_sent.year < datetime.now().year:
                    await channel.send(f"\nHappy birthday {member}! We wish you a special day!\n")
                    c.execute("UPDATE birthdays SET last_sent = ? WHERE user_id = ?", (datetime.now(), user[0]))
                    conn.commit()

    conn.close()

@bot.command()
@commands.has_permissions(administrator=True)
async def delete(ctx, user_id: int):
    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute("SELECT * FROM birthdays WHERE user_id = ?", (user_id,))
    existing_data = c.fetchone()

    if existing_data:
        c.execute("DELETE FROM birthdays WHERE user_id = ?", (user_id,))
        conn.commit()
        await ctx.send("Birthday record deleted successfully!")
    else:
        await ctx.send("User not found in the database.")

    conn.close()

@bot.command()
async def commands(ctx):
    """
    Display all available commands.
    """
    command_list = []

    for command in bot.commands:
        if command.name == 'clear' or command.name == 'sort':
            command_list.append(f"!{command.name} :closed_lock_with_key:")
        elif command.name != 'help':
            command_list.append(f"!{command.name}")

    commands_message = "\n".join(command_list)

    await ctx.send(f"\n{commands_message}\n")
    await ctx.send(f"\n{'More commands coming soon!'}\n")

@bot.command()
async def Help(ctx):
    """
    Help
    """
    help_message = """
    Command: !commands
    Description: Shows all bot commands.

    Command: !Help
    Description: Shows the description of each command.

    Command: !birthday
    Description: Add your birthday in the following format: DD/MM/YY and you 
    will be mentioned on that special day.

    Command: !sort
    Description: Performs a random sorting among members.
    **(This command is allowed in special functions on the server)**

    Command: !clear
    Description: Clears all messages from the current channel. 
    **(This command is allowed in special functions on the server)**

    Command: !links
    Description: Shows all currently available links.
    """

    await ctx.send(f"```\n{help_message}\n```")

keep_alive()
my_secret = os.environ['DISCORD_BOT_SECRET']
bot.run(my_secret)