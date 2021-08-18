import discord
import time
from main import db, randomHexGen
from datetime import datetime, timedelta
from discord.ext import commands
from collections import defaultdict, Counter
import random
import re

from typing import List

pollEmojiList = []
optionList = []
pollStarted = None

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

#➥ Poll View Class
class Poll(discord.ui.View):    
    def __init__(self, ctx, timeout, pollEmojiList, optionList, dictionary, embed):
        super().__init__(timeout = timeout)
        self.optionList = optionList
        self.dictionary = dictionary
        self.embed = embed
        self.ctx = ctx
        
        for emoji, label in zip(pollEmojiList, optionList):
            self.add_item(PollButton(ctx, emoji, label, dictionary, embed))
    
    async def on_timeout(self):
        print(self.dictionary)
        try:
            await self.message.edit(embed = createResultsEmbed(self.ctx, self.dictionary, self.embed), view = None)
        except Exception:
            pass
##
#➥ Custom Button for Polls
class PollButton(discord.ui.Button['Poll']):
    def __init__(self, ctx, emoji, label, dictionary, embed):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji, label = label)
        self.ctx = ctx
        self.emoji = emoji
        self.dictionary = dictionary
        self.pollEmbed = embed

    async def callback(self, interaction: discord.Interaction):
        newPoll = self.dictionary
    #➥ Settings Embed
        if self.ctx.author.id == interaction.user.id: 
            content = ":pencil2: ➙ Edit the Poll \n:grey_question: ➙ Check Your Vote \n:repeat: ➙ Clear your vote\n:closed_lock_with_key: ➙ Toggle if voters are allowed to clear their vote \n:hourglass: ➙ Change the timelimit (Default is 3 Days)\n:detective: ➙ Toggle result anonymity\n<:cancel:851278899270909993> ➙ Close the Poll & Show results"
            isAuthor = True
        else:
            content = """:grey_question: ➙ Check Your Vote \n:repeat: ➙ Clear your vote """
            isAuthor = False
        settingsEmbed = discord.Embed (
            title = "Settings & Poll Info",
            description = content,
            color = randomHexGen()
        )
        settingsEmbed.add_field(name = "You haven't voted yet!", value = '\u200b')
    ##
        if self.emoji.name == 'settings':
            if interaction.user.id in newPoll:
                settingsEmbed.set_field_at(0, name = "Your vote is:", value = str(newPoll.get(interaction.user.id)))
            await interaction.response.send_message(embed = settingsEmbed, view = Settings(self.ctx, isAuthor, newPoll, self.pollEmbed, settingsEmbed, self.view.message), ephemeral = True)
            return
        
        if interaction.user.id not in newPoll:
            newPoll[interaction.user.id] = f"{self.emoji.name} {self.label}"
            numVotes = len(newPoll)
            self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = numVotes)
            await interaction.response.edit_message(embed = self.pollEmbed, view = self.view)
            return
##
#➥ Custom Button for Settings
class SettingsButton(discord.ui.Button['Settings']):
    def __init__(self, ctx, emoji, dictionary, pollEmbed, settingsEmbed, pollMessage):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.ctx = ctx
        self.emoji = emoji
        self.dictionary = dictionary
        self.pollEmbed = pollEmbed
        self.settingsEmbed = settingsEmbed
        self.pollMessage = pollMessage
            
    async def callback(self, interaction: discord.Interaction):
        closedPoll = False
        newPoll = self.dictionary
        isAnon = True if str(self.pollEmbed.author.name) == "Results are Anonymous" else False
        #➥ Detect if poll is closed
        try:
            isLocked_bool = True if self.pollEmbed.fields[2].value == ":unlock:" else False
        except IndexError:
            closedPoll = True
        ##
        
        if closedPoll and not self.emoji.name == '❔':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            return
        
        #➥ If button is lock
        if self.emoji.name == '🔐':
            isLocked_str = ":lock:" if self.pollEmbed.fields[2].value == ":unlock:" else ":unlock:"
            
            self.label = "Unlock" if isLocked_bool else "Lock"
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = isLocked_str)
            self.pollEmbed.set_field_at(2, name = "Poll is", value = isLocked_str)
            await self.pollMessage.edit(embed = self.pollEmbed)        
            
            #➥ Locked Repeat logic
            for button in self.view.children[1:]:
                if isLocked_bool and str(button.emoji) == '🔁':
                    button.disabled = True
                    button.style = discord.ButtonStyle.danger
                elif str(button.emoji) == '🔁':
                    button.disabled = False
                    button.style = discord.ButtonStyle.success
            ##
            await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
            return
        ##
        #➥ If button is detective
        if self.emoji.name == '🕵️‍♂️':
            if isAnon:
                self.settingsEmbed.set_field_at(0, name = "Results are now", value = ":sunny: Shown with names")
                self.pollEmbed.set_author(name = "Results are shown with names", icon_url = "")
                await self.pollMessage.edit(embed = self.pollEmbed) 
            else:
                self.settingsEmbed.set_field_at(0, name = "Results are now", value = ":detective: Anonymous")
                self.pollEmbed.set_author(name = "Results are Anonymous")
                await self.pollMessage.edit(embed = self.pollEmbed) 
            await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
            return
        ##
        #➥ If button is timelimit
        if self.emoji.name == '⌛':
            time = datetime.utcnow()
            await self.pollMessage.delete()
            human_timeout = await self.bot.get_command('waitCheck')(ctx, 90)
            
            view = Poll(self.ctx, timeout, pollEmojiList, optionList, self.dictionary, self.pollEmbed)
            view.message = await self.ctx.send(embed = self.pollEmbed, view = view)
            return
        ##
        
        if str(self.emoji) == '<:cancel:851278899270909993>':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            await self.pollMessage.edit(embed = createResultsEmbed(self.ctx, self.dictionary, self.pollEmbed), view = None)
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            return
        
        # Buttons non-authors can click on    
        if interaction.user.id in newPoll:  
            if self.emoji.name == '❔':
                self.settingsEmbed.set_field_at(0, name = "Your vote is:", value = str(newPoll.get(interaction.user.id)))
                await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view) 
                return
            if self.emoji.name == '🔁' and isLocked_bool:
                del newPoll[interaction.user.id]
                self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = len(newPoll))
                self.settingsEmbed.set_field_at(0, name = "You haven't voted yet!", value = "\u200b")
                await self.pollMessage.edit(embed = self.pollEmbed)
                await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)     
                return 
            else:
                self.settingsEmbed.set_field_at(0, name = "Poll is :lock:", value = "You cannot change your vote")
                await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view) 
                return
        else:
            if self.emoji.name == '❔' or self.emoji.name == '🔁':
                self.settingsEmbed.set_field_at(0, name = "You haven't voted yet!", value = "\u200b")
                await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view) 
                return

##
#➥ Settings View Class
class Settings(discord.ui.View):    
    children: List[SettingsButton]
    def __init__(self, ctx, isAuthor, dictionary, pollEmbed, settingsEmbed, pollMessage):
        super().__init__()       
        isLocked = False if pollEmbed.fields[2].value == ":unlock:" else True
        if isAuthor:
            settings = ['\U0000270f', '\U00002754', '\U0001f501', '<:cancel:851278899270909993>']
            self.add_item(SelectMenu(ctx, dictionary, pollEmbed, settingsEmbed, pollMessage))
        else: settings = ['\U00002754', '\U0001f501']
        
        #➥ Adding Buttons
        for emoji in settings:
            button = SettingsButton(ctx, emoji, dictionary, pollEmbed, settingsEmbed, pollMessage)
            if isLocked and str(button.emoji) == '\U0001f501': #If locked and button refresh
                button.disabled = True #disable
                button.style = discord.ButtonStyle.danger #turn red
            elif str(button.emoji) == '\U0001f501':
                button.style = discord.ButtonStyle.success #turn green
            self.add_item(button)  
        ##
##
#➥ SelectMenu View
class SelectMenu(discord.ui.Select):
    def __init__(self, ctx, dictionary, pollEmbed, settingsEmbed, pollMessage):
        self.timeOption = discord.SelectOption(label="Timelimit", emoji="⌛")
        self.lockedOption = discord.SelectOption(label="Locked", emoji="🔐")
        self.anonOption = discord.SelectOption(label="Anonymity", emoji="🕵️‍♂️")
        
        super().__init__(placeholder = "What would you like to modify?", 
                         options=[self.timeOption, self.lockedOption, self.anonOption])
        
        self.timeButton = SettingsButton(ctx, "⌛", dictionary, pollEmbed, settingsEmbed, pollMessage)
        self.lockedButton = SettingsButton(ctx, "🔐", dictionary, pollEmbed, settingsEmbed, pollMessage)
        self.anonButton = SettingsButton(ctx, "🕵️‍♂️", dictionary, pollEmbed, settingsEmbed, pollMessage)
    
    async def callback(self, interaction: discord.Interaction):
        self.options = [self.timeOption, self.lockedOption, self.anonOption]
        if self.values[0] == "Timelimit":
            self.view.add_item(self.timeButton) #Add the TimeLimit button
            self.options.pop(self.options.index(self.timeOption)) #Remove timelimit from the list of options
            try: self.view.children.pop(self.view.children.index(self.lockedButton)) #Attempt to pop the other buttons
            except Exception: pass
            try: self.view.children.pop(self.view.children.index(self.anonButton))
            except Exception: pass
                
        elif self.values[0] == "Locked":
            self.view.add_item(self.lockedButton)
            self.options.pop(self.options.index(self.lockedOption))
            try: self.view.children.pop(self.view.children.index(self.timeButton))
            except Exception: pass
            try: self.view.children.pop(self.view.children.index(self.anonButton))
            except Exception: pass
            
        elif self.values[0] == "Anonymity":
            self.view.add_item(self.anonButton)
            self.options.pop(self.options.index(self.anonOption))
            try: self.view.children.pop(self.view.children.index(self.timeButton))
            except Exception: pass
            try: self.view.children.pop(self.view.children.index(self.lockedButton))
            except Exception: pass
        return await interaction.response.edit_message(view = self.view)
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
            timeout = 15
            pollStarted = datetime.utcnow()
            pollView = Poll(ctx, timeout, pollEmojiList, fullOptionList, newPoll, embed)
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