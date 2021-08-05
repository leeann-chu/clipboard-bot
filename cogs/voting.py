import discord
from main import db, randomHexGen
from datetime import datetime
from discord.ext import commands
from collections import defaultdict
import random
import re

#➥ humanTime
def humantimeTranslator(s):
    d = {
      'w':      7*24*60*60,
      'week':   7*24*60*60,
      'weeks':  7*24*60*60,
      'd':      24*60*60,
      'day':    24*60*60,
      'days':   24*60*60,
      'h':      60*60,
      'hr':     60*60,
      'hour':   60*60,
      'hours':  60*60,
      'm':      60,
      'minute': 60,
      'minutes':60,
    }
    mult_items = defaultdict(lambda: 1).copy()
    mult_items.update(d)

    parts = re.search(r'^(\d+)([^\d]*)', s.lower().replace(' ', ''))
    if parts:
        return int(parts.group(1)) * mult_items[parts.group(2)] + humantimeTranslator(re.sub(r'^(\d+)([^\d]*)', '', s.lower()))
    else:
        return 0
##

#➥ formatContent
def formatContent(options, emojis):
    pairedList = []
    optionList = options.split("\n")
    emojiList = emojis.split("\n")
    
    for option, emoji in zip(optionList, emojiList):
        pairedList.append(f"{emoji} {option}")
        
    return "\n".join(pairedList)
##

#➥ formatContent
def makeList_removeSpaces(string):
    spaceless = [s for s in string if s != ' ']
    spaceString = "".join(spaceless)
    spaceList = spaceString.split("\n")
    return spaceList
##

#➥ Setting up Cog   
class voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = db
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("voting is Ready")
        
    @commands.group(aliases = ["poll"])
    async def vote(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}poll create` \nSee `{ctx.prefix}poll help` for a list of examples!")
##        
    
    #➥ poll help menu
    @vote.command()
    async def help(self, ctx):
        await ctx.send("""
                       """)
    
    #➥ create poll
    @vote.command(aliases = ["create"])
    async def make(self, ctx, *, title = None):
        pollAuthor = ctx.author
        
    #➥ Setting up the variables for the embed
        if title is None:
            await ctx.send("What would you like the **Title** of your poll to be?")
            title = await self.bot.get_command('waitCheck')(ctx, 100)
            
        await ctx.send("Enter the options for your poll seperated by new lines")
        msg = await self.bot.get_command('waitCheck')(ctx, 200)
        await ctx.send("Enter the emojis you wish to use for your poll seperated by new lines")
        emojis = await self.bot.get_command('waitCheck')(ctx, 300)
    ##
        pairedList = formatContent(msg, emojis)
        
    #➥ Forming the embed
        timestamp = datetime.utcnow()
        embed = discord.Embed(
            title = title,
            description = "React with the corresponding emote to cast a vote. \nVote only once.\n\n" + pairedList,
            color = randomHexGen(),
            timestamp = timestamp
        )
        embed.add_field(name = "\u200b", value = "\u200b", inline = False)
        embed.add_field(name = "Edit the Poll \n(creator only)", value = "➥ :pencil2:")
        embed.add_field(name = "Clear your vote \n& Cast again", value = "➥ :repeat:")
        embed.add_field(name = "Change the timelimit \nDefault is 3 days", value = "➥ :alarm_clock:")
        embed.add_field(name = "Close the Poll \n& Show results", value = "➥ <:cancel:851278899270909993>")
        
        tips = ["Does not work with custom emojis.",
        "You can create polls using ~poll create <Title> to speed things up.",
        "You can set your cooldown using human words, like 1 week 2 days 3 hours.",
        "This embed color has been randomly generated."]
        embed.set_footer(text = random.choice(tips), icon_url=ctx.author.avatar_url)
    ##    
        pollEmbed = await ctx.send(embed = embed)
        
        emojiList = makeList_removeSpaces(emojis)
        
        #Edit Poll
        reactedEmoji = await self.bot.get_command('reactRespond')(ctx, pollEmbed, 180, emojiList, multiple = True)
     
        # if stuff[0].emoji.name == 'cancel':
        #         await ctx.channel.purge(limit = 1)
        #         await ctx.send("Canceled", delete_after = 2)
        # elif emoji == 'alarm_clock':
        #         await ctx.send("How long would you like your poll to be open for? \n(Format: `<number><length>` Examples: `1d`, `5h`, `30m`)")
        #         humanTime = await self.bot.get_command('waitCheck')(ctx, 100)
        #         timeout = humantimeTranslator(humanTime)
        #         pollEmbed.clear_reactions()
        #         stuff = await self.bot.get_command('reactRespond')(ctx, pollEmbed, timeout, emojiList)
                
        
        
    @vote.command(aliases=["append"])
    async def add(self, ctx, embed):
        embed.edit(description = embed.description + "Fleas")

    #➥ timeConvert
    @commands.command()
    async def timeConvert(self, ctx, *, inp: str):
        await ctx.send(humantimeTranslator(inp))
    ##
        
def setup(bot):
    bot.add_cog(voting(bot))