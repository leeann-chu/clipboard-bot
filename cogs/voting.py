import discord
import asyncio
import time
from main import db, randomHexGen
from datetime import datetime, timedelta
from discord.ext import commands
from collections import defaultdict
import random
import re

from typing import List

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

#➥ Custom Button for Polls
class PollButton(discord.ui.Button['PollButton']):
    def __init__(self, ctx, emoji, dictionary, embed):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.ctx = ctx
        self.emoji = emoji
        self.dictionary = dictionary
        self.pollEmbed = embed

    async def callback(self, interaction: discord.Interaction):
        newPoll = self.dictionary
        if self.emoji.name == 'settings':
            #➥ Content
            if self.ctx.author.id == interaction.user.id: 
                content = ":pencil2: ➙ Edit the Poll \n:grey_question: ➙ Check what you voted for \n:repeat: ➙ Clear your vote\n:closed_lock_with_key: ➙ Toggle if voters are allowed to clear their vote \n:alarm_clock: ➙ Change the timelimit (Default is 3 Days)\n<:cancel:851278899270909993> ➙ Close the Poll & Show results"
                isAuthor = True
            else:
                content = """:grey_question: ➙ Check what you voted for \n:repeat: ➙ Clear your vote """
                isAuthor = False
            settingsEmbed = discord.Embed (
                title = "Settings & Poll Info",
                description = content,
                color = randomHexGen()
            )
            settingsEmbed.add_field(name = "Poll Closes on", value="May 8th")
            ##
            await interaction.response.send_message(embed = settingsEmbed, view = Settings(self.ctx, isAuthor, newPoll, self.pollEmbed, settingsEmbed, self.view.message), ephemeral = True)
            return
        
        if interaction.user.id not in newPoll:
            newPoll[interaction.user.id] = self.emoji.name
            numVotes = len(newPoll)
            self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = numVotes)
            await interaction.response.edit_message(embed = self.pollEmbed, view = self.view)
            return
##

#➥ Poll View Class
class Poll(discord.ui.View):    
    def __init__(self, ctx, pollEmojiList, dictionary, embed):
        super().__init__(timeout = 15)
        self.ctx = ctx
        for emoji in pollEmojiList:
            self.add_item(PollButton(ctx, emoji, dictionary, embed))
    
    async def on_timeout(self):
        await self.ctx.send("This poll has closed!")
        self.clear_items()
##

#➥ Custom Button for Settings
class SettingsButton(discord.ui.Button['SettingsButton']):
    def __init__(self, ctx, emoji, dictionary, pollEmbed, settingsEmbed, pollMessage):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.ctx = ctx
        self.emoji = emoji
        self.dictionary = dictionary
        self.pollEmbed = pollEmbed
        self.settingsEmbed = settingsEmbed
        self.pollMessage = pollMessage
            
    async def callback(self, interaction: discord.Interaction):
        newPoll = self.dictionary
            
        # Check Your Vote and Clear your vote
        if interaction.user.id in newPoll:
            if self.emoji.name == '❔':
                await interaction.response.send_message(content = newPoll.get(interaction.user.id), ephemeral = True)
            elif self.emoji.name == '🔁':
                del newPoll[interaction.user.id]
                self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = len(newPoll))
                await self.pollMessage.edit(embed = self.pollEmbed)                
                await interaction.response.send_message("Your vote has been cleared!", ephemeral = True)
        else:
            await interaction.response.send_message("You haven't voted yet!", ephemeral = True)

##
#➥ Settings View Class
class Settings(discord.ui.View):    
    children: List[SettingsButton]
    def __init__(self, ctx, isAuthor, dictionary, pollEmbed, settingsEmbed, pollMessage):
        super().__init__()       
        if isAuthor:
            settings = ['\U0000270f', '\U00002754', '\U0001f510', '\U0001f501', '\U000023f0', '<:cancel:851278899270909993>']
        else: settings = ['\U00002754', '\U0001f501']
            
        for emoji in settings:
            button = SettingsButton(ctx, emoji, dictionary, pollEmbed, settingsEmbed, pollMessage)
            self.add_item(button)      
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
        
    #➥ Setting up the variables for the embed
        if title is None:
            await ctx.send("What would you like the **Title** of your poll to be?")
            title = await self.bot.get_command('waitCheck')(ctx, 100)
            
        await ctx.send("Enter the options for your poll seperated by new lines")
        msg = await self.bot.get_command('waitCheck')(ctx, 200)
        await ctx.send("Enter the emojis you wish to use for your poll seperated by new lines")
        emojis = await self.bot.get_command('waitCheck')(ctx, 300)
        await ctx.channel.purge(limit = 4)
        emojiList = makeList_removeSpaces(emojis)
        if len(emojiList) > 25:
            return await ctx.send("Polls may only have up to 25 options. Try again.")
    ##
        pollEmojiList = emojiList + ['<a:settings:845834409869180938>']
        
    #➥ Forming the embed
        pairedList = formatContent(msg, emojis)
        timestamp = discord.utils.utcnow()
        embed = discord.Embed(
            title = title,
            description = "React with the corresponding emote to cast a vote. \n\n" + pairedList,
            color = randomHexGen(),
            timestamp = timestamp
        )
        embed.add_field(name = "Votes Recorded:", value = 0)
        #➥ Footer
        tips = ["Tip #1: Does not work with emojis from outside the current server",
        f"Tip #2: You can create polls using \"{ctx.prefix}poll create <Title>\" to speed things up",
        "Tip #3: You can set your cooldown using human words, like \"1 week 2 days 3 hours\"",
        "Tip #4: This embed color has been randomly generated",
        "Tip #5: Only the poll creator can edit or close the poll",
        "Tip #6: The default time limit for a poll is 3 days",
        "Tip #7: Polls can have up to 25 options",
        f"Tip #8: During Poll Creation dialogue you can input \"{ctx.prefix}cancel\" to exit",
        "Tip #9: Locked polls can not have their votes changed"
        "Tip #10: Click on the settings button to find out more information about this poll"]
        # Get my current profile pic
        member = ctx.guild.get_member(364536918362554368)
        embed.set_footer(text = random.choice(tips), icon_url = member.avatar.url)
        ##
    ##  
        try:
            newPoll = {}
            pollView = Poll(ctx, pollEmojiList, newPoll, embed)
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