import discord
from discord.errors import InteractionResponded
from main import randomHexGen
from poll_class import *
from cogs.menusUtil import *
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from collections import defaultdict, Counter
import random
import json
import re

from typing import List

emojiList = []
optionList = []
newPoll = {}
isOpenPoll = False

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

#➥ format_toString
def format_toString(options, emojis):
    pairedString = []
    oList = options.split("\n")
    eList = emojis.split("\n")
    
    for option, emoji in zip(oList, eList):
        pairedString.append(f"{emoji} {option}")
        
    return "\n".join(pairedString)
##

#➥ remove spaces
def makeList_removeSpaces(string):
    splitList = string.split("\n")
    spaceless = [s.strip() for s in splitList]
    return spaceless
##

#➥ Poll View Class
class Poll(discord.ui.View):    
    def __init__(self, ctx, clipboardBot, emojiList, optionList, embed):
        super().__init__(timeout = None)
        
        for emoji, label in zip(emojiList, optionList):
            self.add_item(PollButton(ctx, clipboardBot, emoji, label, embed))
##
#➥ Custom Button for Polls
class PollButton(discord.ui.Button['Poll']):
    def __init__(self, ctx, clipboardBot, emoji, label, embed):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji, label = label)
        self.ctx = ctx
        self.clipboardBot = clipboardBot
        self.emoji = emoji
        self.pollEmbed = embed

    async def callback(self, interaction: discord.Interaction):
        time = discord.utils.utcnow()
        discordTimestamp = self.pollEmbed.fields[1].value
        timestamp = re.findall('\d+', discordTimestamp)
        
        closedPoll = time >= datetime.fromtimestamp(int(timestamp[0]), tz = timezone.utc)
        
        if closedPoll:
            resultsEmbed = await self.clipboardBot.bot.get_command('createResultsEmbed')(self.ctx, self.pollEmbed)
            self.view.stop()
            await interaction.response.edit_message(embed = resultsEmbed, view = None)
            return
        
    #➥ Settings Embed
        if self.ctx.author.id == interaction.user.id: 
            content = "<:white_plus:878169238932684831> ➙ Add options to the poll \n:grey_question: ➙ Check your vote \n:repeat: ➙ Clear your vote\n<:cancel:851278899270909993> ➙ Close the Poll \n\n:closed_lock_with_key: ➙ Toggle if voters are allowed to clear their vote \n:hourglass: ➙ Change when the poll closes (Default is 1 Day)\n:detective: ➙ Toggle anonymity\n:printer: ➙ See who has voted"
            isAuthor = True
        else:
            content = ":grey_question: ➙ Check Your Vote \n:repeat: ➙ Clear your vote \n:printer: ➙ See who has voted"
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
            await interaction.response.send_message(embed = settingsEmbed, view = Settings(self.ctx, self.clipboardBot, isAuthor, self.pollEmbed, settingsEmbed, self.view.message), ephemeral = True)
            return
        
        if interaction.user.id not in newPoll:
            newPoll[interaction.user.id] = f"{self.emoji.name} {self.label}"
            numVotes = len(newPoll)
            self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = numVotes)
            await interaction.response.edit_message(embed = self.pollEmbed, view = self.view)
            
            followup = discord.Embed (title = "You have voted for option:" + str(self.emoji),
                                      description = "If you would like to change your vote please use the :repeat: button\nFor more information use :grey_question:")
            await interaction.followup.send(embed = followup, view = Settings(self.ctx, self.clipboardBot, isAuthor, self.pollEmbed, settingsEmbed, self.view.message), ephemeral = True)
            return
        if interaction.user.id in newPoll:
            followup = discord.Embed (title = "You have already voted!",
                                      description = "If you would like to see what you voted for try :grey_question:\nIf you would like to change your vote use :repeat:")
            await interaction.response.send_message(embed = followup, view = Settings(self.ctx, self.clipboardBot, isAuthor, self.pollEmbed, settingsEmbed, self.view.message), ephemeral = True)
        
##
#➥ Custom Button for Settings
class SettingsButton(discord.ui.Button['Settings']):
    def __init__(self, ctx, clipboardBot, emoji, pollEmbed, settingsEmbed, pollMessage):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.ctx = ctx
        self.clipboardBot = clipboardBot
        self.emoji = emoji
        self.pollEmbed = pollEmbed
        self.settingsEmbed = settingsEmbed
        self.pollMessage = pollMessage
            
    async def callback(self, interaction: discord.Interaction):
        closedPoll = False
        isAnon = True if str(self.pollEmbed.author.name) == "Results are Anonymous" else False
        #➥ Detect if poll is closed
        try:
            isLocked_bool = True if self.pollEmbed.fields[2].value == ":unlock:" else False
        except IndexError:
            closedPoll = True
        ##
        
        if closedPoll and not self.emoji.name == '❔':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            self.settingsEmbed.set_footer(text = "You can dismiss this message now")
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
            global emojiList, optionList
            fullEmojiList = emojiList + ['<a:settings:845834409869180938>']
            fullOptionList = optionList + ["Settings"]
            
            pollStarted = self.pollEmbed.timestamp
            view = Confirm()
            try: await self.pollMessage.delete() 
            except: pass
            
            self.settingsEmbed.title = "Please enter how long you want the poll to be open for"
            self.settingsEmbed.description = "Examples: `1d2h`, `3 hours`, `1 h`"
            self.settingsEmbed.set_field_at(0, name = "Poll was started at", value = f"<t:{int(pollStarted.timestamp())}:f>")
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            
            human_timeout = await self.clipboardBot.bot.get_command('waitCheck')(self.ctx, 90)
            timeout = humantimeTranslator(human_timeout)            
            pollClose = pollStarted + timedelta(seconds =+ timeout)
            self.settingsEmbed.title = "Poll is now set to close at"
            self.settingsEmbed.description = f"<t:{int(pollClose.timestamp())}:f>"
            self.settingsEmbed.clear_fields()
            self.settingsEmbed.set_footer(text = "Is this what you wanted?")
            await interaction.edit_original_message(embed = self.settingsEmbed, view = view)
            await self.ctx.channel.purge(limit=1)
            
            await view.wait()
            if view.value == None:
                return await self.ctx.send(f"Confirmation menu timed out!", delete_after = 3)
            elif view.value:
                self.settingsEmbed.set_footer(text = "You can dismiss this message now")
                await interaction.edit_original_message(embed = self.settingsEmbed, view = self.view) 
 
                self.pollEmbed.set_field_at(1, name = "Date Poll Closes:", value = f"<t:{int(pollClose.timestamp())}:f>")
                
                pollView = Poll(self.ctx, self.clipboardBot, fullEmojiList, fullOptionList, self.pollEmbed)              
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")
            else:
                self.settingsEmbed.title = "Canceled Menu"
                self.settingsEmbed.description = "You can dismiss this message now"
                await interaction.followup.send(embed = self.settingsEmbed, ephemeral=True)
                          
                pollView = Poll(self.ctx, self.clipboardBot, fullEmojiList, fullOptionList, self.pollEmbed)              
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")
            return
        ##
        #➥ If button is print
        if self.emoji.name == '🖨':
            if newPoll:
                results = []
                for key in newPoll:
                        member = self.ctx.guild.get_member(int(key))
                        results.append(f"[{member.display_name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") has voted")
                embed = discord.Embed(title = "Here's a list of people who have voted so far!", description = "\n".join(results), color = randomHexGen())
                await interaction.response.edit_message(embed = embed)
            else:
                await interaction.response.edit_message("No one has voted yet!")
        ##
        
        #➥ If button is edit
        if self.emoji.name == '➕':
            await interaction.response.defer()
            view = Confirm()
            oldEmojiList = emojiList
            oldOptionList = optionList
            try: await self.pollMessage.delete() 
            except: pass
            
            optionPrompt = await self.ctx.send("Enter the new options you want to add seperated by new lines")
            msg = await self.clipboardBot.bot.get_command('waitCheck')(self.ctx, 200)
            if msg == None: return
            await optionPrompt.delete()
            
            emojiPrompt = await self.ctx.send("Enter the new emojis you want to add seperated by new lines")
            emojis = await self.clipboardBot.bot.get_command('waitCheck')(self.ctx, 300)
            if emojis == None: return
            await emojiPrompt.delete()
            
            emojiList = emojiList + makeList_removeSpaces(emojis)
            optionList = optionList + makeList_removeSpaces(msg)
            if len(emojiList) > 25:
                return await self.ctx.send("Polls may only have up to 25 options. Try again.")
            
            pairedString = format_toString("\n".join(optionList), "\n".join(emojiList))
            
            self.settingsEmbed.title = "Does this look about right?"
            self.settingsEmbed.clear_fields()
            self.settingsEmbed.description = pairedString
            confirmationMenu = await interaction.followup.send(embed = self.settingsEmbed, view = view)
            
            await view.wait()
            if view.value == None:
                await confirmationMenu.delete()
                return await self.ctx.send(f"Confirmation menu timed out!", delete_after = 3)
            elif view.value:
                await confirmationMenu.delete()
                fullEmojiList = emojiList + ['<a:settings:845834409869180938>']
                fullOptionList = optionList + ['Settings']
                self.pollEmbed.description = "React with the corresponding emote to cast a vote. \n\n" + pairedString
                pollView = Poll(self.ctx, self.clipboardBot, fullEmojiList, fullOptionList, self.pollEmbed)              
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")  
            else:
                await confirmationMenu.delete()
                self.settingsEmbed.title = "Canceled Menu"
                self.settingsEmbed.description = "You can dismiss this message now"
                await interaction.followup.send(embed = self.settingsEmbed, ephemeral=True)
                
                fullEmojiList = oldEmojiList + ['<a:settings:845834409869180938>']
                fullOptionList = oldOptionList + ['Settings']            
                pollView = Poll(self.ctx, self.clipboardBot, fullEmojiList, fullOptionList, self.pollEmbed)              
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")  
            return
        ##
        
        #➥ If button is cancel
        if str(self.emoji) == '<:cancel:851278899270909993>':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            self.settingsEmbed.set_footer(text = "You can dismiss this message now")
            resultsEmbed = await self.clipboardBot.bot.get_command('createResultsEmbed')(self.ctx, self.pollEmbed)
            await self.pollMessage.edit(embed = resultsEmbed, view = None)
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            return
        ##
        #➥ Buttons non-authors can click on    
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
##
#➥ Settings View Class
class Settings(discord.ui.View):    
    children: List[SettingsButton]
    def __init__(self, ctx, clipboardBot, isAuthor, pollEmbed, settingsEmbed, pollMessage):
        super().__init__()       
        isLocked = False if pollEmbed.fields[2].value == ":unlock:" else True
        if isAuthor:
            settings = ['\U00002795', '\U00002754', '\U0001f501', '<:cancel:851278899270909993>']
            self.add_item(SelectMenu(ctx, clipboardBot, pollEmbed, settingsEmbed, pollMessage))
        else: settings = ['\U00002754', '\U0001f501', '\U0001f5a8']
        
        #➥ Adding Buttons
        for emoji in settings:
            button = SettingsButton(ctx, clipboardBot, emoji, pollEmbed, settingsEmbed, pollMessage)
            if str(button.emoji) == '<:cancel:851278899270909993>':
                button.style = discord.ButtonStyle.danger #turn red
            if str(button.emoji) == '\U00002795':
                button.style = discord.ButtonStyle.primary #turn blurple
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
    def __init__(self, ctx, clipboardBot, pollEmbed, settingsEmbed, pollMessage):
        self.timeOption = discord.SelectOption(label="Timelimit", emoji="⌛")
        self.lockedOption = discord.SelectOption(label="Locked", emoji="🔐")
        self.anonOption = discord.SelectOption(label="Anonymity", emoji="🕵️‍♂️")
        self.printOption = discord.SelectOption(label="Print Who Voted", emoji="🖨")
        
        super().__init__(placeholder = "What would you like to modify?", 
                         options=[self.timeOption, self.lockedOption, self.anonOption, self.printOption])
        
        self.timeButton = SettingsButton(ctx, clipboardBot, "⌛", pollEmbed, settingsEmbed, pollMessage)
        self.lockedButton = SettingsButton(ctx, None, "🔐", pollEmbed, settingsEmbed, pollMessage)
        self.anonButton = SettingsButton(ctx, None, "🕵️‍♂️", pollEmbed, settingsEmbed, pollMessage)
        self.printButton = SettingsButton(ctx, clipboardBot, "🖨", pollEmbed, settingsEmbed, pollMessage)
    
    async def callback(self, interaction: discord.Interaction):
        self.options = [self.timeOption, self.lockedOption, self.anonOption, self.printOption]
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
            
        elif self.values[0] == "Print Who Voted":
            self.view.add_item(self.printButton)
            self.options.pop(self.options.index(self.printOption))
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
    @vote.command(aliases = ["create", "start", "new", "c", "m", "s"])
    async def make(self, ctx, *, title = None):
        await ctx.trigger_typing() 
        member = ctx.guild.get_member(ctx.author.id)
        embed = discord.Embed(description="")
        embed.set_author(name = ctx.author)
        
    # #➥ Check that a poll hasn't already been created
    #     global isOpenPoll
    #     if isOpenPoll:
    #         return await ctx.send("Please close the previous poll before starting a new one!")
        
    #➥ Setting up the variables for the embed
        if title is None:
            embed.description = "What would you like the **Title** of your poll to be?"
            embed.set_footer(text="This question will time out in 3 minutes") 
            titlePrompt = await ctx.send(embed = embed)
            title = await self.bot.get_command('waitCheck')(ctx, 180)
            await titlePrompt.delete()
        
        if "\n" not in title:
            embed.title = "Enter the options for your poll seperated by *new lines*"
            embed.description = "Please make sure the options are all in one single message"
            embed.set_footer(text=f"This question will time out in 6 minutes | You can type {ctx.prefix}cancel to cancel")
            optionPrompt = await ctx.send(embed = embed)
            msg = await self.bot.get_command('waitCheck')(ctx, 400)
            if msg == None: return
            await optionPrompt.delete()
            
            embed.title = ("Enter the emojis you wish to use for your poll seperated by *new lines*")
            embed.description = "You probably should only use the default emojis or emojis from the current server"
            embed.set_footer(text=f"This question will time out in 6 minutes | You can type {ctx.prefix}cancel to cancel")
            emojiPrompt = await ctx.send(embed = embed)
            emojis = await self.bot.get_command('waitCheck')(ctx, 400)
            if emojis == None: return
            await emojiPrompt.delete()
        else:
            entirePoll = title
            title = title.split("\n", 1)[0]
            emojis = "\n".join(re.findall(r"^[^*](?!\w)", entirePoll, re.MULTILINE))
            msg = "\n".join(re.findall(r"[\w\s()'-]+$", entirePoll, re.MULTILINE)[1:])
            
        global emojiList
        global optionList
        emojiList = makeList_removeSpaces(emojis)
        optionList = makeList_removeSpaces(msg)
        if len(emojiList) > 25:
            return await ctx.send("Polls may only have up to 24 options. Try making the Poll again.")
        if len(emojiList) != len(optionList):
            return await ctx.send("You have an unmatched number of options and emojis. Try making the Poll again.")
    ##
    #➥ Forming the embed
        pairedString = format_toString(msg, emojis)
        timestamp = discord.utils.utcnow()
        embed = discord.Embed(
            title = title,
            description = "React with the corresponding emote to cast a vote. \n\n" + pairedString,
            color = randomHexGen(),
            timestamp = timestamp
        )
        pollClose = timestamp + timedelta(seconds =+ 86400)
        embed.add_field(name = "Votes Recorded:", value = 0)
        embed.add_field(name = "Date Poll Closes:", value=f"<t:{int(pollClose.timestamp())}:f>")
        embed.add_field(name = "Poll is", value = ":unlock:")
        
        embed.set_author(name = "Results are Anonymous")
        #➥ Footer
        tips = ["Tip #1: Does not work with emojis from outside the current server",
        f"Tip #2: You can create polls using \"{ctx.prefix}poll create <Title>\" to speed things up",
        "Tip #3: You can set the timelimit using human words, like \"1 week 2 days 3 hours\"",
        "Tip #4: This embed color has been randomly generated",
        "Tip #5: Only the poll creator can edit or close the poll",
        "Tip #6: The default time limit for a poll is 1 day",
        "Tip #7: Polls can have up to 25 options",
        f"Tip #8: During Poll Creation dialogue you can input \"{ctx.prefix}cancel\" to exit",
        "Tip #9: Locked polls cannot have their votes changed",
        "Tip #10: Click on the settings button to find out more information about this poll",
        "Tip #11: You can hover over the nicknames in the results to see their username (if the poll is not anonymous)"]
        embed.set_footer(text = random.choice(tips), icon_url = member.avatar.url)
        ##
    ##  
        try:
            global newPoll
            isOpenPoll = True
            fullEmojiList = emojiList + ['<a:settings:845834409869180938>']
            fullOptionList = optionList + ["Settings"]
            pollView = Poll(ctx, self, fullEmojiList, fullOptionList, embed)
            pollView.message = await ctx.send(embed = embed, view = pollView) 
        except Exception as e:
            print(e)
            return await ctx.send("One of your emojis is invalid! Try making the Poll again.")        
##            

    #➥ timeConvert
    @commands.command()
    async def timeConvert(self, ctx, *, inp: str):
        seconds = humantimeTranslator(inp)
        await ctx.send(seconds)
    ##  
    
    #➥ Create Results Embed
    @commands.command()
    @commands.is_owner()
    async def createResultsEmbed(self, ctx, embed):
        pollClosingTime = embed.fields[1].value
        global isOpenPoll
        isOpenPoll = False
        
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
            
            for key, values in newPoll.items():
                    member = ctx.guild.get_member(key)
                    results.append(f"[{member.display_name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") voted {values}")
            privateEmbed = discord.Embed(title = "Here are the Results!", description = "\n".join(results), color = randomHexGen())
            if isAnon and len(newPoll) > 1: await ctx.guild.get_member(ctx.bot.owner_id).send(embed = privateEmbed)
            
            #➥ Results
            if isAnon:
                results.clear()
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
            if len(winners) == 1:
                embed.add_field(name = "The winner is...", value = winners[0], inline = False)
            else:
                embed.add_field(name = "The winners...", value = "\n".join(winners), inline = False)
                embed.add_field(name = "As there was a tie, one has been chosen at random from our winners", value = random.choice(winners), inline = False) 
        ##
        embed.add_field(name = "Date Poll Started:", value = f"<t:{int(embed.timestamp.timestamp())}:f>")
        embed.add_field(name = "Date Poll Closed:", value = pollClosingTime)
        newPoll.clear()
        return embed
    ##
    
    #➥ Vote example command
    @vote.command()
    async def example(self, ctx):
        await ctx.guild.get_member(ctx.author.id).send("https://imgur.com/a/wq6swYo")
    ##
    
    # ➥ Print the dictionary
    @vote.command()
    @commands.is_owner()
    async def print(self, ctx):
        results = []
        for key, values in newPoll.items():
                member = ctx.guild.get_member(int(key))
                results.append(f"[{member}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") voted {values}")
        privateEmbed = discord.Embed(title = "Here are the Results!", description = "\n".join(results), color = randomHexGen())
        await ctx.guild.get_member(ctx.bot.owner_id).send(embed = privateEmbed) 
        return privateEmbed
    ##
    #➥ Insert dictionary
    @vote.command()
    @commands.is_owner()
    async def insertPoll(self, ctx, *, inp : str):
        global newPoll
        newPoll = json.loads(inp.replace("'", "\""))    
        await ctx.send("Dictionary inserted")
    ##
    #➥ Clear dictionary
    @vote.command()
    @commands.is_owner()
    async def clear(self):
        newPoll.clear()
    ##
    #➥ Submit Image
    @vote.command()
    async def submit(self, ctx):
        message = ctx.message
        embed = discord.Embed(title = "Is this correct?", color = randomHexGen())
        try: 
            embed.set_image(url = message.attachments[0])  
        except Exception:
            return await ctx.send("Please attach an image with this command!")  
        view = Confirm()
        msg = await ctx.send(embed = embed, view = view)
        await view.wait()
        if view.value is None:
            return await ctx.send(f"Confirmation menu timed out!", delete_after = 3)
        elif view.value:
            await msg.edit(embed = embed, view = None)
            with open("image_urls.json", 'r') as f:
                images = json.load(f)
            images[str(ctx.author.id)] = message.attachments[0].url
            with open("image_urls.json", 'w') as f:
                json.dump(images, f, indent = 4)
            await ctx.send("Image successfully submitted!")
        else:
            await msg.edit(embed = embed, view = None)
            return await ctx.send(f"Submission canceled", delete_after = 3)
    ##
    
def setup(bot):
    bot.add_cog(voting(bot))