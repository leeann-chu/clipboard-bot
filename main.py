import discord
import os
import random
import json
from API_KEYS import *
from discord.ext import commands
from datetime import datetime

description = "I can store long term, short term, and immediate goals!"
# intents = discord.Intents.default()
# intents.members = True

def get_prefix(bot, message):
    with open("prefixes.json", 'r') as f:
        prefixes = json.load(f)
        
        return prefixes[str(message.guild.id)]

#➥ randomHexGen
def randomHexGen():
    # Create a random hex value
    r = random.randint(0, 16777215)
    return int(hex(r), base=16)
##

bot = commands.Bot(command_prefix=get_prefix, description=description)
bot.remove_command('help')

#➥ on ready command
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type= discord.ActivityType.listening, name="you forget your milk"))
    print("Logged in as {0.user}".format(bot))
    print("------------------------------")
##

#➥ .json manipulation
@bot.event
async def on_guild_join(guild):
    with open("prefixes.json", 'r') as f:
        prefixes = json.load(f)
    # Default guild value, the prefix all servers should start with
    prefixes[str(guild.id)] = '~'
    with open("prefixes.json", 'w') as f:
        json.dump(prefixes, f, indent = 4)

@bot.event
async def on_guild_remove(guild):
    with open("prefixes.json", 'r') as f:
        prefixes = json.load(f)
    prefixes.pop(str(guild.id))
    with open("prefixes.json", 'w') as f:
        json.dump(prefixes, f, indent = 4)
##

#➥ Prefix Checker
@bot.event
async def on_message(message):
    prefix = get_prefix(bot, message)
    if message.author == bot.user:
        return
    if message.content.startswith('~help'):
        await message.channel.send(f'To bring up help menu type `{prefix}chelp` <:blush:845843091146539008>')
    await bot.process_commands(message)
##

#➥ Help command
@bot.command()
async def chelp(ctx):
    await ctx.trigger_typing()

    # Get server prefix
    prefix = get_prefix(bot, ctx)

    member = ctx.message.author
    embed = discord.Embed(
        description = "Help menu for all your clipboard commands",
        color = randomHexGen(),
        timestamp = datetime.utcnow()
    )

    embed.set_author(name="Here to help!", icon_url="https://cdn.discordapp.com/attachments/809686249999826955/845595120639672320/bigBirdy.gif")
    embed.add_field(name="<a:settings:845834409869180938> Useful Commands", 
        value=(f"""[`{prefix}avatar`](https://www.tumblr.com/blog/view/magnificenttyger "Works with nicknames ex: {prefix}avatar {member.display_name}") ⇀ Returns user's avatar
                   [`{prefix}clear x`](https://www.tumblr.com/blog/view/magnificenttyger "Aliases: delete, purge") ⇀ Clears x number of messages (defaults to 10)
                    `{prefix}info` ⇀ Tells you more about this bot
                    `{prefix}joined` ⇀ Returns info about when user joined
                    `{prefix}ping` ⇀ Returns ping
                    `{prefix}prefix` ⇀ Edit the prefix used for commands on this server
                 """), 
                 inline=True)
    embed.add_field(name="<a:partyParrot:845597006898659328> Fun Commands", 
        value=f"""`{prefix}add` ⇀ Adds two numbers together ex: `{prefix}add 3 4` 
                 [`{prefix}8ball`](https://www.tumblr.com/blog/view/magnificenttyger "Aliases: 8b") ⇀ Ask <:8ball:845546744665735178> questions   
                """,        
                inline=True)

    await ctx.send(embed=embed)
##    

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

#➥ Clear Command and Error
@bot.command(name="clear", aliases=["purge", "delete"])
@commands.has_permissions(manage_guild=True)
async def clear(ctx, amount=10):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Cleared {amount} messages!", delete_after = 5)

@clear.error
async def clear_error(ctx, error):
    member = ctx.message.author
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"sorry {member.display_name}, you do not have permission to clear messages!", delete_after = 3)
##

#➥ Info command
@bot.command()
async def info(ctx):
    await ctx.trigger_typing()
    
    # Get my current profile pic
    member = await ctx.guild.fetch_member("364536918362554368")
    pfp = member.avatar_url

    # Get server prefix
    prefix = get_prefix(bot, ctx)

    # Create Embed
    embed = discord.Embed(
        title = "📋 Clipboard Bot Information", 
        description = description + f"\nThis server's prefix is `{prefix}`", 
        color = randomHexGen()
    )
    #embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="__Functionalities__", value="• timer to send a reminder \n• check things off the list \n• create sticky reminders \n• create persistent reminders", inline=False)
    embed.set_footer(text="Created by GracefulLion", icon_url=pfp)

    await ctx.send(embed=embed)
##

#➥ Server prefix set command
@bot.command()
@commands.has_permissions(manage_guild=True)
async def prefix(ctx):
    prefix = get_prefix(bot, ctx)
    embed = discord.Emed(
        title = "<a:settings:845834409869180938> Changing Server Prefix",
        description = f"The **current** standard prefix is `{prefix}`\n\nPlease enter the new prefix:",
        color = randomHexGen()
    )

    with open("prefixes.json", 'r') as f:
        prefixes = json.load(f) 
    prefixes[str(ctx.guild.id)] = prefix
    with open("prefixes.json", 'w') as f:
        json.dump(prefixes, f, indent = 4)

    await ctx.send(f"Successfully changed **standard prefix** to: `{prefix}`")

@prefix.error
async def prefix_error(ctx, error):
    member = ctx.message.author
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"sorry {member.display_name}, you do not have permission edit server prefix!", delete_after = 3)
##

#➥ loading and unloading
@bot.command(name="reload")
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    print(f'{extension} is reloaded!')
    await ctx.send(f'{extension} is reloaded!')

for filename in os.listdir("./cogs"):
    if filename.endswith('.py'):
        #takes .py files and cuts off their extension
        bot.load_extension(f'cogs.{filename[:-3]}')

# @reload.error
# async def reload_error(ctx, error):
#     print("reload error")
#     extensionErrors = (commands.ExtensionNotLoaded, commands.ExtensionNotFound, )
#     if isinstance(error, extensionErrors):
#         await ctx.send(f"Unrecognized Extension!")

##

bot.run(BOT_TOKEN)