import discord
import time
from main import db, randomHexGen
from cogs.menusUtil import *
from datetime import datetime, timedelta
from discord.ext import commands
from collections import defaultdict, Counter
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

#➥ formatString
def formatString(options, emojis):
    pairedList = []
    optionList = options.split("\n")
    emojiList = emojis.split("\n")
    
    for option, emoji in zip(optionList, emojiList):
        pairedList.append(f"{emoji} {option}")
        
    return "\n".join(pairedList)
##

#➥ remove spaces
def makeList_removeSpaces(string):
    splitList = string.split("\n")
    spaceless = [s.strip() for s in splitList]
    return spaceless
##

#➥ Create Results Embed
def createResultsEmbed(ctx, newPoll, embed):
    isAnon = True if str(embed.author.name) == "Results are Anonymous" else False
    results = []
    winners = []
    if newPoll:
        #➥ Winner Logic
        freqDict = Counter(newPoll.values()) #Find the # votes for each emoji
        maxNum = list(freqDict.values())[0]
        winnerDict = {k: v for k, v in freqDict.items() if v == maxNum} #Turn it into a dict to cycle through
        for key in winnerDict:
            winners.append(key) #Add winners with the most votes to winner list
        ##
        
        #➥ Results
        if not isAnon:
            for key, values in newPoll.items():
                member = ctx.guild.get_member(key)
                results.append(f"[{member.display_name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") voted {values}")
        else:
            for key, values in winnerDict.items():
                if values != 1:
                    results.append(f"{key} has {values} votes")
                else:
                    results.append(f"{key} has {values} vote")
        ##
    
    #➥ Forming the embed
    embed.title = "Here are the Results!"
    embed.description = "\n".join(results) if results else "No one voted!"
    embed.clear_fields()
    
    if results:
        embed.add_field(name = "The winner is..." if len(winners) == 1 else "The winners are...", value = "\n".join(winners), inline = False)
    ##
    return embed
##

#➥ Setting up Cog   
class voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("voting is Ready")
        
    @commands.group(aliases = ["poll", "v", "p"])
    async def vote(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}poll create`")
##        
    
    #➥ poll help menu
    @vote.command()
    async def help(self, ctx):
        await ctx.send(f"Use the command `{ctx.prefix}poll create` or \n`{ctx.prefix}poll create <Title>` to get started!")
    ##
    
#➥ ------------   Create Poll   ------------
    @vote.command(aliases = ["create", "start", "new"])
    async def make(self, ctx, *, title = None):
        await ctx.trigger_typing() 
        
    #➥ Setting up the variables for the embed
        if title is None:
            await ctx.send("What would you like the **Title** of your poll to be?")
            title = await self.bot.get_command('waitCheck')(ctx, 100)
            
        await ctx.send("Enter the options for your poll seperated by new lines")
        msg = await self.bot.get_command('waitCheck')(ctx, 200)
        if msg == None: return
        await ctx.send("Enter the emojis you wish to use for your poll seperated by new lines")
        emojis = await self.bot.get_command('waitCheck')(ctx, 300)
        if emojis == None: return
        
        #➥ check for deleting messages
        def isPollAuthor(msg):
            return msg.author == ctx.author and ctx.channel == msg.channel
        ##
        await ctx.channel.purge(limit = 4, check=isPollAuthor)
        emojiList = makeList_removeSpaces(emojis)
        optionList = makeList_removeSpaces(msg)
        if len(emojiList) > 25:
            return await ctx.send("Polls may only have up to 25 options. Try again.")
    ##
        pollEmojiList = emojiList + ['<a:settings:845834409869180938>']
        fullOptionList = optionList + ['Settings']
    #➥ Forming the embed
        pairedList = formatString(msg, emojis)
        embed = discord.Embed(
            title = title,
            description = "React with the corresponding emote to cast a vote. \n\n" + pairedList,
            color = randomHexGen(),
            timestamp = discord.utils.utcnow()
        )
        embed.add_field(name = "Votes Recorded:", value = 0)
        embed.add_field(name = "Poll Closes on", value="May 8th")
        embed.add_field(name = "Poll is", value = ":unlock:")
        
        embed.set_author(name = "Results are Anonymous")
        #➥ Footer
        tips = ["Tip #1: Does not work with emojis from outside the current server",
        f"Tip #2: You can create polls using \"{ctx.prefix}poll create <Title>\" to speed things up",
        "Tip #3: You can set your cooldown using human words, like \"1 week 2 days 3 hours\"",
        "Tip #4: This embed color has been randomly generated",
        "Tip #5: Only the poll creator can edit or close the poll",
        "Tip #6: The default time limit for a poll is 3 days",
        "Tip #7: Polls can have up to 25 options",
        f"Tip #8: During Poll Creation dialogue you can input \"{ctx.prefix}cancel\" to exit",
        "Tip #9: Locked polls can not have their votes changed",
        "Tip #10: Click on the settings button to find out more information about this poll",
        "Tip #11: You can hover over the nicknames in the results to see their username"]
        # Get my current profile pic
        member = ctx.guild.get_member(ctx.author.id)
        embed.set_footer(text = random.choice(tips), icon_url = member.avatar.url)
        ##
    ##  
        try:
            newPoll = {}
            pollView = Poll(ctx, pollEmojiList, fullOptionList, newPoll, embed)
            pollView.message = await ctx.send(embed = embed, view = pollView) 
        except Exception as e:
            print(e)
            return await ctx.send("One of your emojis is invalid! Try again.")        
##            
    
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