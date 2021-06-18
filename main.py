import discord
import os
import random
import json
import asyncio
import asyncpg
from API_KEYS import *
from discord.ext import commands
from datetime import datetime

description = "I can store long term, short term, and immediate goals!"
credentials = {"user": USERNAME, "password": PASSWORD, "database": DATABASE, "host": "127.0.0.1"}

#➥ randomHexGen
def randomHexGen():
    # Create a random hex value
    return random.randint(0, 16777215)
##

def get_prefix(bot, message):
    if message.guild is None:
        return "~"
    else:
        with open("prefixes.json", 'r') as f:
            prefixes = json.load(f)
        return prefixes[str(message.guild.id)]
    
loop = asyncio.get_event_loop()
db = loop.run_until_complete(asyncpg.create_pool(**credentials))
bot = commands.Bot(command_prefix=get_prefix, description=description, activity=discord.Activity(type= discord.ActivityType.listening, name="you forget your milk"), db=db)   


#➥ on ready command
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
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
    if message.content.startswith(('~help', f'{prefix}help')):
        await message.channel.send(f'To bring up detailed help menu type `{prefix}chelp` <:blush:845843091146539008>')
    await bot.process_commands(message)
##

#➥ Help command
@bot.command()
async def chelp(ctx, argument = None):
    await ctx.trigger_typing()

    # Get server prefix
    prefix = ctx.prefix
    member = ctx.message.author
    m = ctx.message
    
    #➥ Get hover text
    with open("helpmenu.json", 'r') as f:
        helpmenu = json.load(f)

    # These are variables because formatting deal with it
    avatar = helpmenu["avatar"]
    clear = helpmenu["clear"]
    add = helpmenu["add"]
    repeat = helpmenu["repeat"]
    _8ball = helpmenu["8ball"]
    ##
        
    if argument is None:
#➥ Embed for Empty Argument
        embed = discord.Embed(
            description = f"Help menu for all your clipboard commands\nHover over the command to see more info or type `{prefix}chelp [command]` for more help",
            color = randomHexGen(),
            timestamp = datetime.utcnow()
        )

        embed.set_author(name="Here to help!", icon_url="https://cdn.discordapp.com/attachments/809686249999826955/845595120639672320/bigBirdy.gif")
        embed.add_field(name="<a:settings:845834409869180938> Useful Commands", 
            value=(f"""[`{prefix}avatar`](https://www.tumblr.com/blog/view/magnificenttyger "{avatar}") ⇀ Returns user's avatar
                    [`{prefix}clear x`](https://www.tumblr.com/blog/view/magnificenttyger "{clear}") ⇀ Clears x number of messages (default is 10)
                        `{prefix}info` ⇀ Tells you more about this bot
                        `{prefix}joined` ⇀ Returns info about when user joined
                        `{prefix}ping` ⇀ Returns ping
                        `{prefix}prefix` ⇀ Edit the prefix used for commands on this server
                    """), 
                    inline=True)
        embed.add_field(name="<a:pugpls:846829754036256808> Fun Commands", 
            value=f"""[`{prefix}add`](https://www.tumblr.com/blog/view/magnificenttyger "{add}") ⇀ Adds two numbers together, takes two arguments 
                    [`{prefix}repeat`](https://www.tumblr.com/blog/view/magnificenttyger "{repeat}") ⇀ Repeats user input
                    [`{prefix}8ball`](https://www.tumblr.com/blog/view/magnificenttyger "{_8ball}") ⇀ Ask <:8ball:845546744665735178> questions   
                    """,        
                    inline=True)

        await ctx.send(embed=embed)
    ##
    elif argument in bot.all_commands:
    #➥ Help per command
        command = bot.get_command(argument)
        if (argument) == "avatar":
            await ctx.send(f"{avatar}")
        elif (argument) == "clear":
            await ctx.send(f"{clear}")
        elif (argument) == "add":
            await ctx.send(f"{add}")
        elif (argument) == "repeat":
            await ctx.send(f"{repeat}")
        elif (argument) == "8ball":
            await ctx.send(f"{_8ball}")
    ##        
    else:
        await ctx.send("Unrecognized command")
##    

#➥ Close Bot
@bot.command()
async def quit(ctx):
    if await bot.is_owner(ctx.author):
        await bot.change_presence(status = discord.Status.offline)
        await db.close()
        await bot.logout()
    else:
        await ctx.send("You do not have the permissions to use this command!")
##

#➥ Ping
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")
##

#➥ Info command
@bot.command()
async def info(ctx):
    await ctx.trigger_typing()
    
    # Get my current profile pic
    member = await ctx.guild.fetch_member("364536918362554368")
    pfp = member.avatar_url

    # Get server prefix
    prefix = ctx.prefix

    # Create Embed
    embed = discord.Embed(
        title = "📋 Clipboard Bot Information", 
        description = description + f"\nThis server's prefix is `{prefix}`", 
        color = randomHexGen()
    )
    #embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="__Functionalities__", value="• timer to send a reminder \n• check things off the list \n• create sticky reminders \n• create persistent reminders", inline=False)
    embed.set_footer(text="Created by GracefulLion", icon_url=pfp)

    await ctx.send(embed = embed)
##

#➥ loading and unloading
@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx, *, extension: str):
    eList = extension.split(" ")
    for extension in eList:
        bot.unload_extension(f'cogs.{extension}')
        bot.load_extension(f'cogs.{extension}')
        print(f'{extension} is reloaded!')
        await ctx.send(f'Extension {extension} is reloaded!')

for filename in os.listdir("./cogs"):
    if filename.endswith('.py'):
        #takes .py files and cuts off their extension
        bot.load_extension(f'cogs.{filename[:-3]}')

@reload.error
async def reload_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
    extensionErrors = (commands.ExtensionNotLoaded, commands.ExtensionNotFound, commands.MissingRequiredArgument, )
    if isinstance(error, extensionErrors):
        await ctx.send(f"Unrecognized Extension!")
    else: 
        print("\nSome other Error!")
        raise error

##

bot.run(BOT_TOKEN)