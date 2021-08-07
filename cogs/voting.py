import discord
import asyncio
import time
from main import db, randomHexGen
from datetime import datetime, timedelta
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

#➥ VotingDictionary
class VotingDictionary:
    def __init__(self):
        self.votes = {}
    def addVote(self, member, reaction):
        self.votes[member] = reaction
        
    def hasVoted(self, member):
        return member in self.votes
    
    def getVote(self, member):
        return self.votes.get(member)
        
    def removeVote(self, member):
        del self.votes[member]
        
    def displayResults(self):
        return self.votes 
##

#➥ --To Remove: Count Class with Buttons 
class Count(discord.ui.View):
    @discord.ui.button(label = '0', style=discord.ButtonStyle.red)
    async def count(self, button: discord.ui.Button, interaction: discord.Interaction):
        number = int(button.label) if button.label else 0
        if number + 1 >= 5:
            button.style = discord.ButtonStyle.green
            button.disabled = True
        button.label = str(number + 1)

        # Make sure to update the message with our updated selves
        await interaction.response.edit_message(view=self)
##

#➥ Custom Button for Polls
class PollButton(discord.ui.Button['VoteReaction']):
    def __init__(self, emoji):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.emoji = emoji
    
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: PollButton = self.view
        await interaction.response.send_message("You vote for..." + str(self.emoji), view=self, ephemeral=True)
##

#➥ Poll View Class
class Poll(discord.ui.View):    
    def __init__(self, emojiList):
        super().__init__()
        for emoji in emojiList:
            self.add_item(PollButton(emoji))
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

#➥ remove spaces
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
    ##
    
#➥ ------------   Create Poll   ------------
    @vote.command(aliases = ["create", "start", "new"])
    async def make(self, ctx, *, title = None):
        await ctx.trigger_typing() 
        pollAuthor = ctx.author
        
    #➥ Setting up the variables for the embed
        if title is None:
            await ctx.send("What would you like the **Title** of your poll to be?")
            title = await self.bot.get_command('waitCheck')(ctx, 100)
            
        await ctx.send("Enter the options for your poll seperated by new lines")
        msg = await self.bot.get_command('waitCheck')(ctx, 200)
        await ctx.send("Enter the emojis you wish to use for your poll seperated by new lines")
        emojis = await self.bot.get_command('waitCheck')(ctx, 300)
        emojiList = makeList_removeSpaces(emojis)
        if len(emojiList) > 25:
            return await ctx.send("Polls may only have up to 25 options. Try again.")
    ##
        
        settings = ['\U0000270f', '\U0001f501', '\U000023f0', '\U00002754', '<:cancel:851278899270909993>']
        finalList = emojiList + settings
        
    #➥ Forming the embed
        pairedList = formatContent(msg, emojis)
        timestamp = discord.utils.utcnow()
        embed = discord.Embed(
            title = title,
            description = "React with the corresponding emote to cast a vote. \nVote only once.\n\n" + pairedList,
            color = randomHexGen(),
            timestamp = timestamp
        )
        embed.add_field(name = "\u200b", value = "\u200b", inline = False)
        embed.add_field(name = "Edit the Poll", value = "➥ :pencil2:")
        embed.add_field(name = "Clear your vote \n& Cast Again", value = "➥ :repeat:")
        embed.add_field(name = "Change the timelimit \nDefault is 3 days", value = "➥ :alarm_clock:")
        embed.add_field(name = "Check your vote", value = "➥ :grey_question:")
        embed.add_field(name = "Close the Poll \n& Show results", value = "➥ <:cancel:851278899270909993>")
        #➥ Footer
        tips = ["Does not work with custom emojis.",
        "You can create polls using ~poll create <Title> to speed things up.",
        "You can set your cooldown using human words, like 1 week 2 days 3 hours.",
        "This embed color has been randomly generated.",
        "Only the poll creator can edit or close the poll",
        "The default time limit for a poll is 3 days",
        "If your reaction isn't automatically removed try again",
        "The poll can only have 25 options"]
        # Get my current profile pic
        member = ctx.guild.get_member(364536918362554368)
        embed.set_footer(text = random.choice(tips), icon_url = member.avatar.url)
        ##
    ##  
        newPoll = VotingDictionary()  
        try:
            pollEmbed = await ctx.send(embed = embed, view = Poll(finalList)) 
        except Exception as e:
            print(e)
            return await ctx.send("One of your emojis is invalid! Try again.")
        
    #➥ Timer Things - wait_time 10 seconds
        start = datetime.utcnow()
        wait_time = 10
        time_left = wait_time - (datetime.utcnow() - start).seconds
    ##

        while time_left > 0: 
            time.sleep(1)
            # try:
            #     reaction, user = await self.bot.wait_for('reaction_add', timeout = time_left, check = checkEmoji)            
            #     person = user.id
            #     vote = str(reaction)
            #➥ Record vote in dictionary
                #newPoll.addVote(member.id, reaction)
            ##                         
            # except asyncio.TimeoutError:
            #     await view.clear_items()
            #     await ctx.send("This Poll has closed!")
                
            time_left = wait_time - (datetime.utcnow() - start).seconds
        
        print(newPoll.displayResults())
        await ctx.send("This Poll has closed!")
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