import discord
import random
from utils.API_KEYS import BOT_TOKEN
from discord.ext import commands
from utils.poll_class import readfromFile, writetoFile
from utils.models import Session

description = "I can store long term, short term, and immediate goals!"
db = Session()

#* randomHexGen
def randomHexGen():
    # Create a random hex value
    return random.randint(0, 16777215)
##

def get_prefix(bot, message):
    try:
        if message.guild is None:
            return "~"
        else:
            prefixes = readfromFile("prefixes")
            return prefixes[str(message.guild.id)]
    except KeyError:
        return "~"

intents = discord.Intents.default()  # All but the two privileged ones
intents.members = True  # Subscribe to the Members intent
bot = commands.Bot(command_prefix=get_prefix, description=description, activity=discord.Activity(
    type=discord.ActivityType.listening, name="you forget your milk"), intents=intents, db=db)
bot.remove_command('help')

#* on ready command
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("------------------------------")
##

#* .json manipulation
@bot.event
async def on_guild_join(guild):
    prefixes = readfromFile("prefixes")
    # Default guild value, the prefix all servers should start with
    prefixes[str(guild.id)] = '~'
    writetoFile(prefixes, "prefixes")

@bot.event
async def on_guild_remove(guild):
    prefixes = readfromFile("prefixes")
    prefixes.pop(str(guild.id))
    writetoFile(prefixes, "prefixes")
##

#* Help command
@bot.command(aliases = ["chelp"])
async def help(ctx, argument=None):
    await ctx.trigger_typing()

    # Get server prefix
    prefix = ctx.prefix

    if argument is None:
        # * Embed for Empty Argument
        embed = discord.Embed(
            description=f"Help menu for all your clipboard commands\nHover over the command to see more info",
            color=randomHexGen(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name="Here to help!", icon_url="https://cdn.discordapp.com/attachments/809686249999826955/845595120639672320/bigBirdy.gif")
        
        embed.add_field(name="<:voteicon:881035523102236684> Voting Commands",
                        value=(f"""[`{prefix}poll create`](https://i.imgur.com/dV7GBcih.jpg \"Aliases: v make, vote create, p make, vote start, p m...\") ➙ Guides you through making a poll
                               `{prefix}poll create <Title>` ➙ Speeds things along 
                               `{prefix}poll example` ➙ Sends you a dm with an example being created
                               `{prefix}poll submit` ➙ DM the bot with this command and an attached image to submit your image to the poll
                               """))
        
        embed.add_field(name="<a:settings:845834409869180938> Useful Commands",
                        value=(f"""[`{prefix}avatar`](https://i.imgur.com/dV7GBcih.jpg "Works with nicknames or usernames. ex: {prefix}avatar Graceless") ➙ Returns user's avatar
                    [`{prefix}clear x`](https://i.imgur.com/dV7GBcih.jpg "Aliases: {prefix}purge") ➙ Clears x number of messages (default is 10)
                        `{prefix}info` ➙ Tells you more about this bot
                        `{prefix}joined` ➙ Returns info about when user joined
                        `{prefix}ping` ➙ Returns ping
                        `{prefix}prefix` ➙ Edit the prefix used for commands on this server
                    """),
                        inline=True)
                        
        embed.add_field(name="<a:pugpls:846829754036256808> Fun Commands",
                        value=(f"""[`{prefix}add`](https://i.imgur.com/dV7GBcih.jpg "Aliases: math. ex: {prefix}add 3 4 6") ➙ Adds numbers together 
                    [`{prefix}repeat`](https://i.imgur.com/dV7GBcih.jpg "Aliases: mimic, copy. ex: {prefix}repeat doot") ➙ Repeats user input
                    [`{prefix}8ball`](https://i.imgur.com/dV7GBcih.jpg "Aliases: 8b") ➙ Ask <:8ball:845546744665735178> questions   
                    """),
                        inline=True)

        await ctx.send(embed=embed)
##

#* Close Bot
@bot.command(aliases = ["close"])
async def quit(ctx):
    if await bot.is_owner(ctx.author):
        await ctx.send("Bot is Closed!")
        await bot.close()
        await db.close()
    else:
        await ctx.send("You do not have the permissions to use this command!")
##

#* Ping
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")
##

#* Cancel
@bot.command()
async def cancel(ctx):
    await ctx.send("Action has been canceled",  delete_after = 3)
##

#* Info command
@bot.command()
async def info(ctx):
    await ctx.trigger_typing()

    # Get my current profile pic
    member = ctx.guild.get_member(364536918362554368)
    pfp = member.avatar.url

    # Get server prefix
    prefix = ctx.prefix

    # Create Embed
    embed = discord.Embed(
        title="📋 Clipboard Bot Information",
        description=description + f"\nThis server's prefix is `{prefix}`",
        color=randomHexGen()
    )
    #embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name="__Functionalities__",
                    value="• timer to send a reminder \n• check things off the list \n• create sticky reminders \n• create persistent reminders", inline=False)
    embed.add_field(name="__Changelog__",
                    value = """Voting Bot Changelog: 
                                *Among other things*
                                • Prints an ephemeral message when a user votes to give them feedback that their vote was registered successfully along with other instructions 
                                • Included a new button for non-poll owners to see who has voted so far
                                • A new way to create polls that is much faster
                                • now randomly chooses a winner if there's a tie
                                """)
    embed.set_footer(text="Created by GracefulLion", icon_url=pfp)

    await ctx.send(embed=embed)
##

#* loading and unloading
@bot.command(aliases = ["Reload"])
@commands.is_owner()
async def reload(ctx, *, extension: str):
    eList = extension.split(" ")
    for extension in eList:
        bot.unload_extension(f'cogs.{extension}')
        bot.load_extension(f'cogs.{extension}')
        print(f'{extension} is reloaded!')
        await ctx.send(f'Extension {extension} is reloaded!')

cogsList = ["botFun", "clipboard", "error_handler", "utilities", "voting"]
for cog in cogsList:
    bot.load_extension(f'cogs.{cog}')

@reload.error
async def reload_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
    extensionErrors = (commands.ExtensionNotLoaded,
                       commands.ExtensionNotFound, commands.MissingRequiredArgument, )
    if isinstance(error, extensionErrors):
        await ctx.send(f"Unrecognized Extension!")
    else:
        print("\nSome other Error!")
        raise error

##

bot.run(BOT_TOKEN)
