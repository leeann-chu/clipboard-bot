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
    print("We have logged in as {0.user}".format(bot))
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

#➥ command_error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown Command. Type ~help for list of commands")
##

#➥ Help command
@bot.command()
async def chelp(ctx):
    await ctx.trigger_typing()
    member = ctx.message.author
    embed = discord.Embed(
        description = "Help menu for all your clipboard commands",
        color = randomHexGen(),
        timestamp = datetime.utcnow()
    )
    embed.set_author(name="Here to help!", icon_url="https://cdn.discordapp.com/attachments/809686249999826955/845595120639672320/bigBirdy.gif")
    embed.add_field(name="<:gear:845597637877039106> Useful Commands", 
        value=(f"""`~ping` ⇀ Returns ping
                 [`~clear x`](https://www.tumblr.com/blog/view/magnificenttyger "Aliases: delete, purge") ⇀ Clears x number of messages (defaults to 10)
                 `~joined` ⇀ Returns info about when user joined
                 `~avatar` ⇀ Returns user's avatar, also works with nicknames ex: `~avatar {member.display_name}`
                 `~info` ⇀ Tells you more about this bot
                 """), 
                 inline=False)
    embed.add_field(name="<a:partyParrot:845597006898659328> Fun Commands", 
        value="""[`~8ball`](https://www.tumblr.com/blog/view/magnificenttyger "Aliases: 8b") ⇀ Ask <:8ball:845546744665735178> questions
                 `~add` ⇀ Adds two numbers together ex: `~add 3 4`      
                """,        
                inline=False)

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

#➥ info command
@bot.command()
async def info(ctx):
    await ctx.trigger_typing()
    
    # Get my current profile pic
    member = await ctx.guild.fetch_member("364536918362554368")
    pfp = member.avatar_url

    # Create Embed
    embed = discord.Embed(
        title = "📋 Clipboard Bot Information", 
        description = description, 
        color = randomHexGen())
    #embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="__Functionalities__", value="• timer to send a reminder \n• check things off the list \n• create sticky reminders \n• create persistent reminders", inline=False)
    embed.set_footer(text="Created by GracefulLion", icon_url=pfp)

    await ctx.send(embed=embed)
##

#➥ server prefix set command
@bot.command()
async def prefix(ctx, prefix):
    with open("prefixes.json", 'r') as f:
        prefixes = json.load(f)
   # await ctx.send(f"The **current** standard prefix is {prefixes.peek(str(ctx.guild.id))}")
    prefixes[str(guild.id)] = prefix
    with open("prefixes.json", 'w') as f:
        json.dump(prefixes, f, indent = 4)

    await ctx.send(f"Successfully changed **standard prefix** to: {prefix}!")
    
#➥ loading and unloading
@bot.command()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} is reloaded!')

for filename in os.listdir("./cogs"):
    if filename.endswith('.py'):
        #takes .py files and cuts off their extension
        bot.load_extension(f'cogs.{filename[:-3]}')
##

bot.run(BOT_TOKEN)