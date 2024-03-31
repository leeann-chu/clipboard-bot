import random
from datetime import datetime
from termcolor import colored
import discord
from discord.ext import commands
from myutils.API_KEYS import BOT_TOKEN
from myutils.poll_class import readfromFile, writetoFile
from myutils.models import Session
from myutils.views import EmbedPageView

db = Session()
override = "^"
description = "I can store long term, short term, and immediate goals!"

#* randomHexGen
def randomHexGen():
    # Create a random hex value
    return random.randint(0, 16777215)
##

def get_prefix(bot, message):
    try:
        if message.guild is None:
            return "~" # in dms
        else:
            prefixes = readfromFile("prefixes")
            server_prefix = prefixes[str(message.guild.id)] # normal server
            if message.author.id == 364536918362554368:
                prefix_list = [server_prefix, "~"] # it's me, baby
                return prefix_list            
            return server_prefix
    except KeyError:
        return "~"

intents = discord.Intents.all()  # All but the two privileged ones
intents.members = True  # Subscribe to the Members intent
TEST_GUILD = discord.Object(416749994163568641)

class clipboardBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, description=description, activity=discord.Activity(
    type=discord.ActivityType.listening, name="you forget your milk"), intents=intents, db=db)
        self.cogsList = ["botFun", "clipboard", "category_org", "error_handler", "utilities", "voting"]
        self.recentExt = None

        # self.tree = commands.Bot.tree # used for slash commands

    async def setup_hook(self) -> None:
        await self.tree.sync(guild=TEST_GUILD)
        for cog in self.cogsList:
            await self.load_extension(f'cogs.{cog}')

    #* on ready command
    async def on_ready(self):
        print(f"Logged in as {colored(bot.user, 'green')}")
        print("------------------------------")
        print(colored(f"Using discord.py: {discord.__version__}", 'yellow'))               
    ##

    #* .json manipulation
    async def on_guild_join(self, guild):
        prefixes = readfromFile("prefixes")
        # Default guild value, the prefix all servers should start with
        prefixes[str(guild.id)] = '~'
        writetoFile(prefixes, "prefixes")

    async def on_guild_remove(self, guild):
        prefixes = readfromFile("prefixes")
        prefixes.pop(str(guild.id))
        writetoFile(prefixes, "prefixes")
    ##

    async def close(self):
        await super().close()

bot = clipboardBot()
bot.remove_command('help')

@bot.command()
async def help(ctx):
    p = ctx.prefix

    embed = discord.Embed(
        title="Help Directory",
        description = f"""
    <:splat:860541072102916136> ➙ `{p}corpseHelp`
    <a:Birdy:845590890240278579> ➙ `{p}chelp`
    :notepad_spiral: ➙ `{p}list help`
    <:voteicon:881035523102236684> ➙ `{p}chelp`/`{p}vote help`
    :clipboard: ➙ `{p}info` (deprecated)
    """,
        color=randomHexGen()
    )

    await ctx.send(embed=embed)

#* Help command
@bot.command()
async def chelp(ctx, argument=None):
    p = ctx.prefix

    if argument is None:
        PageOneembed = discord.Embed(
            description="Help menu for all your clipboard commands\nHover over the command to see more info",
            color=randomHexGen(),
            timestamp=discord.utils.utcnow()
        )
        PageOneembed.set_footer(text="Page 1/2")
        PageOneembed.set_author(
            name="Here to help!", icon_url="https://cdn.discordapp.com/attachments/809686249999826955/845595120639672320/bigBirdy.gif")

        PageOneembed.add_field(name="<:voteicon:881035523102236684> Voting Commands",
                        value=(f"""[`{p}poll create`](https://i.imgur.com/dV7GBcih.jpg \"Aliases: v make, vote create, p make, vote start, p m...\") ➙ Guides you through making a poll
                               `{p}poll create <Title>` ➙ Speeds things along
                               `{p}poll example` ➙ Sends you a dm with an example being created
                               """))

        PageOneembed.add_field(name="📋 Clipboard Commands",
                        value=(f"""\n __Creation & Viewing__
                                    `{p}list make` ➙ Create your first List!
                                    `{p}view <title>` ➙ Just shows your list, plain and simple
                                    `{p}list view` ➙ Menu to select which list you wish to view & edit
                                    \n__List & Task Editing__
                                    `{p}list rename <title>` ➙ Renaming lists
                                    `{p}list delete <title>` ➙ Deleting lists
                                    `{p}tasks complete <title>` ➙ Brings up checkoff tasks menu
                                    `{p}tasks add <title>` ➙ Add more tasks to your list
                                    `{p}tasks delete <title>` ➙ Brings up delete tasks menu
                                    \n__Other__
                                    `{p}list example` ➙ Examples of shortcuts you can take to make lists
                                    `{p}list help` ➙ More info on the commands!
                                    """), inline=False)
        PageTwoembed = discord.Embed(
            description="Help menu for all your clipboard commands\nHover over the command to see more info",
            color=randomHexGen(),
            timestamp=discord.utils.utcnow()
        )
        PageTwoembed.set_footer(text="Page 2/2")
        PageTwoembed.set_author(
            name="Here to help!", icon_url="https://cdn.discordapp.com/attachments/809686249999826955/845595120639672320/bigBirdy.gif")
        PageTwoembed.add_field(name="<a:settings:845834409869180938> Useful Commands",
                        value=(f"""[`{p}avatar`](https://i.imgur.com/dV7GBcih.jpg "Works with nicknames or usernames. ex: {p}avatar Graceless") ➙ Returns user's avatar
                    [`{p}clear x`](https://i.imgur.com/dV7GBcih.jpg "Aliases: {p}purge") ➙ Clears x number of messages (default is 10)
                        `{p}info` ➙ Tells you more about this bot
                        `{p}joined` ➙ Returns info about when user joined
                        `{p}ping` ➙ Returns ping
                        `{p}prefix` ➙ Edit the prefix used for commands on this server
                    """),
                        inline=True)

        PageTwoembed.add_field(name="<a:pugpls:846829754036256808> Fun Commands",
                        value=(f"""[`{p}math <operator>`](https://i.imgur.com/dV7GBcih.jpg "Ex: {p}math + 3 4 6") ➙ Adds numbers together
                    [`{p}repeat`](https://i.imgur.com/dV7GBcih.jpg "Aliases: mimic, copy. ex: {p}repeat doot") ➙ Repeats user input
                    [`{p}8ball`](https://i.imgur.com/dV7GBcih.jpg "Aliases: 8b") ➙ Ask 🎱 questions
                    [`{p}emojify`](https://i.imgur.com/dV7GBcih.jpg "Aliases: emoji") ➙ Allows you to use emojis outside of the current server from handpicked list
                    """),
                        inline=True)
        embedList = [PageOneembed, PageTwoembed]
        embedView = EmbedPageView(eList = embedList, pagenum = 0)
        embedView.message = await ctx.send("",embed=PageOneembed, view = embedView)
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
    # Get my current profile pic
    member = ctx.guild.get_member(364536918362554368)
    pfp = member.avatar.url

    # Get server prefix
    prefix = ctx.prefix

    # Create Embed
    embed = discord.Embed(
        title="📋 Clipboard Bot Information-- OUTDATED",
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
async def reload(ctx, *, ext: str = None):
    if ext: # given extension in command
        extension = ext
        bot.recentExt = extension
    else: # no given extension
        if bot.recentExt: # use most recent reloaded extension
            extension = bot.recentExt
        else:
            return await ctx.send(f"Unrecognized Extension: `{ext}`!")

    await bot.unload_extension(f'cogs.{extension}')
    await bot.load_extension(f'cogs.{extension}')
    print(f'{datetime.now()}: {extension} is reloaded!')
    await ctx.send(f'Extension {extension} is reloaded!')

@reload.error
async def reload_error(ctx, error):
    if isinstance(error, commands.errors.NotOwner):
        return await ctx.send("Nice Try.")
        
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
    extensionErrors = (commands.ExtensionNotLoaded,
                       commands.ExtensionNotFound, commands.MissingRequiredArgument, )
    if isinstance(error, extensionErrors):
        return await ctx.send("Unrecognized Extension!")
    else:
        print("\nSome other Error!")
        raise error
#

if __name__ == "__main__": #note to future me bot.run needs to be in name == main
    bot.run(BOT_TOKEN)
