import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import json, asyncio, random, os

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()
intents = discord.Intents.all()
intents.message_content = True


def load_prefixes():
    with open('config.json', 'r') as f:
        data = json.load(f)
        return data.get('prefix', [])

prefix = load_prefixes()
async def get_prefix(bot, message):
    return prefix

bot = commands.Bot(command_prefix=get_prefix, help_command=None, intents=intents)
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"
points_dict = {}

def load_points():
    global points_dict
    try:
        with open('points.json', 'r') as file:
            points_dict = json.load(file)
    except FileNotFoundError:
        points_dict = {}

def spoints():
    with open('points.json', 'w') as file:
        json.dump(points_dict, file, indent=4)

async def update_roles(member: discord.Member, points: int):
    guild = member.guild
    role_ids = {
        150: 1270392297305014415,
        300: 1270392295983812628,
        700: 1270392295379959818,
        1500: 1270392294515802214,
        3500: 1270433149356212225
    }
    roles_to_remove = []
    for threshold, role_id in sorted(role_ids.items(), reverse=True):
        role = discord.utils.get(guild.roles, id=role_id)
        if role in member.roles:
            if points < threshold:
                roles_to_remove.append(role)

    if roles_to_remove:
        await member.remove_roles(*roles_to_remove)

    for threshold, role_id in sorted(role_ids.items(), reverse=True):
        if points >= threshold:
            role = discord.utils.get(guild.roles, id=role_id)
            if role and role not in member.roles:
                await member.add_roles(role)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    load_points()
    await bot.load_extension('jishaku')
    await bot.change_presence(activity=discord.Streaming(name=config['status'],  url=f'https://www.twitch.tv/{config["twitch"]}'))

async def check_admin(ctx):
    if not ctx.author.guild_permissions.administrator:
        color = int(config['embed_color'], 16)
        embed = discord.Embed(description=f"😈 {ctx.author.mention}: Nu poti folosi aceasta comanda", color=color)
        reply = await ctx.reply(embed=embed)
        return False
    return True
active_users = {}

@bot.command()
async def help(ctx):
    if not await check_admin(ctx):
        return
    
    guild = ctx.guild
    color = int(config['embed_color'], 16)
    embed = discord.Embed(
        title="asK - Help",
        description=(
            "$ping - Vezi conexiunea bot - discord\n"
            "$leaderboard - Top 10 membri cu cele mai multe puncte\n"
            "$reset - Reseteaza punctele cuiva\n"
            "$lose - Scade 50 de puncte de la un pierzator\n"
            "$duel - Lupta-te intr-un duel avansat cu cineva\n"
            "$win - Adauga 50 de puncte unui castigator\n"
            "$points - Verifica cate puncte are o persoana"
        ), 
        color=color
    )
    
    if guild:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    if not await check_admin(ctx):
        return
    await ctx.send(f'... `{bot.latency * 1000:.2f} ms`')

@bot.command()
async def win(ctx, member: discord.Member = None):
    if not await check_admin(ctx):
        return

    if member is None:
        color = int(config['embed_color'], 16)
        embed = discord.Embed(description="Usage: `$win [user]`", color=color)
        await ctx.reply(embed=embed)
        return

    if str(member.id) not in points_dict:
        points_dict[str(member.id)] = 0
    points_dict[str(member.id)] += 50
    spoints()

    color = int(config['embed_color'], 16)
    embed = discord.Embed(description=f"😈 {ctx.author.mention}: {member.mention} a primit **50** de puncte!", color=color)
    await ctx.send(embed=embed)

@bot.command()
async def reset(ctx, member: discord.Member = None):
    if not await check_admin(ctx):
        return

    if member is None:
        await ctx.send("Usage: `$reset [user]`")
        return

    points_dict[str(member.id)] = 0
    spoints()

    color = int(config['embed_color'], 16)
    embed = discord.Embed(description=f"Punctele lui {member.mention} au fost resetate!", color=color)
    await ctx.send(embed=embed)

@bot.command()
async def lose(ctx, member: discord.Member = None):
    if not await check_admin(ctx):
        return

    if member is None:
        await ctx.send("Usage: `$lose [user]`")
        return

    if str(member.id) not in points_dict:
        points_dict[str(member.id)] = 0
    points_dict[str(member.id)] -= 50
    spoints()
    
    color = int(config['embed_color'], 16)
    embed = discord.Embed(description=f"😈 {ctx.author.mention}: {member.mention} a pierdut **50** de puncte", color=color)
    await ctx.send(embed=embed)

@bot.command()
async def set(ctx, member: discord.Member = None, amount: int = None):
    if not await check_admin(ctx):
        return

    if member is None or amount is None:
        await ctx.send("Usage: `$set [user] [amount]`")
        return

    points_dict[str(member.id)] = amount
    spoints()
    color = int(config['embed_color'], 16)
    embed = discord.Embed(description=f"😈 {ctx.author.mention} a setat punctele lui {member.mention} la **{amount}**!", color=color)
    await ctx.send(embed=embed)

@bot.command()
async def points(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    if str(member.id) in points_dict:
        points = points_dict[str(member.id)]
        color = int(config['embed_color'], 16)
        embed = discord.Embed(description=f"😈 {ctx.author.mention}: {member.mention} are **{points}** puncte.", color=color)
        await ctx.send(embed=embed)        
        await update_roles(member, points)
    else:
        color = int(config['embed_color'], 16)
        embed = discord.Embed(description=f"😈 {ctx.author.mention}: {member.mention} are **0** de puncte", color=color)
        await ctx.reply(embed=embed)

@bot.command(aliases=['lb'])
async def leaderboard(ctx):
    color = int(config['embed_color'], 16)
    guild = ctx.guild

    filtered_points = {k: v for k, v in points_dict.items() if v >= 1}    
    sorted_points = sorted(filtered_points.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="Top 10 Leaderboard", color=color)
    
    if guild:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    
    leaderboard_text = ""
    for i, (member_id, score) in enumerate(sorted_points[:10], start=1):
        member = ctx.guild.get_member(int(member_id))
        if member:
            leaderboard_text += f"``{i}.`` {member.display_name} - **{score}** puncte\n"
        else:
            leaderboard_text += f"``{i}.`` <@!{member_id}> - **{score}** puncte\n"

    if not leaderboard_text:
        leaderboard_text = "Nu sunt membri cu puncte suficiente pentru a fi afișați."

    embed.description = leaderboard_text
    await ctx.send(embed=embed)

bot.run(config['token'])
