import discord, traceback
from main import randomHexGen
from utils.poll_class import PollClass, SettingsClass, writetoFile, readfromFile
from utils.views import Confirm
from datetime import datetime, timedelta, timezone, date
from discord.ext import commands
from collections import defaultdict, Counter
import random
import json
import re

from typing import List

#* humanTime
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

#* format_toString
def format_toString(options, emojis):
    pairedString = []
    oList = options.split("\n")
    eList = emojis.split("\n")

    for option, emoji in zip(oList, eList):
        pairedString.append(f"{emoji} {option}")

    return "\n".join(pairedString)

#* remove spaces
def makeList_removeSpaces(string):
    splitList = string.split("\n")
    spaceless = [s.strip() for s in splitList]
    return spaceless

#* Poll View Class
class Poll(discord.ui.View):
    def __init__(self, currentPoll):
        super().__init__(timeout = None)

        for emoji, label in zip(currentPoll.emojiList, currentPoll.optionList):
            button = PollButton(currentPoll, emoji, label)
            if str(button.emoji) == '<a:settings:845834409869180938>':
                button.style = discord.ButtonStyle.primary
            self.add_item(button)

#* Custom Button for Polls
class PollButton(discord.ui.Button['Poll']):
    def __init__(self, currentPoll, emoji, label):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji, label = label)
        self.ctx = currentPoll.ctx
        self.currentPoll = currentPoll
        self.clipboardBot = currentPoll.clipboardBot
        self.emoji = emoji
        self.pollEmbed = currentPoll.pollEmbed

    async def callback(self, interaction: discord.Interaction):
        currPoll = readfromFile("storedPolls")
        time = discord.utils.utcnow()
        discordTimestamp = self.pollEmbed.fields[1].value
        timestamp = re.findall('\d+', discordTimestamp)

        closedPoll = time >= datetime.fromtimestamp(int(timestamp[0]), tz = timezone.utc)

        if closedPoll:
            try:
                resultsEmbed = await self.clipboardBot.bot.get_command('createResultsEmbed')(self.currentPoll)
            except Exception:
                print(traceback.format_exc())
                errorFile = open("data\error.txt","a")
                errorFile.write(traceback.format_exc())
                errorFile.close()
                return
            self.view.stop()
            await interaction.response.edit_message(embed = resultsEmbed, view = None)
            return

    #* Settings Embed
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
        currentSettings = SettingsClass(settingsEmbed, self.view.message, isAuthor)

        if self.emoji.name == 'settings':
            if str(interaction.user.id) in currPoll:
                currentSettings.settingsEmbed.set_field_at(0, name = "Your vote is:", value = str(currPoll.get(str(interaction.user.id))))
            await interaction.response.send_message(embed = settingsEmbed, view = Settings(self.currentPoll, currentSettings), ephemeral = True)
            return

        # Not in Poll yet
        if str(interaction.user.id) not in currPoll:
            currPoll[interaction.user.id] = f"{self.emoji.name} {self.label}"
            writetoFile(currPoll, "storedPolls")
            numVotes = len(currPoll)
            self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = numVotes)
            await interaction.response.edit_message(embed = self.pollEmbed, view = self.view)
            self.currentPoll.pollEmbed = self.pollEmbed
            followup = discord.Embed (title = "You have voted for option: " + str(self.emoji),
                                      description = "If you would like to change your vote please use the :repeat: button\nFor more information use :grey_question:")

            await interaction.followup.send(embed = followup, view = Settings(self.currentPoll, currentSettings), ephemeral = True)
            return
        # Already in Poll
        if str(interaction.user.id) in currPoll:
            followup = discord.Embed (title = "You have already voted!",
                                      description = "If you would like to see what you voted for try :grey_question:\nIf you would like to change your vote use :repeat:")
            await interaction.response.send_message(embed = followup, view = Settings(self.currentPoll, currentSettings), ephemeral = True)

#* Custom Button for Settings
class SettingsButton(discord.ui.Button['Settings']):
    def __init__(self, emoji, currentPoll, currentSettings):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.ctx = currentPoll.ctx
        self.clipboardBot = currentPoll.clipboardBot
        self.pollEmbed = currentPoll.pollEmbed
        self.settingsEmbed = currentSettings.settingsEmbed
        self.pollMessage = currentSettings.message
        self.currentPoll = currentPoll

    async def callback(self, interaction: discord.Interaction):
        closedPoll = False
        currPoll = readfromFile("storedPolls")

        #* Detect if poll is closed
        try:
            isLocked_bool = True if self.pollEmbed.fields[2].value == ":unlock:" else False
        except IndexError:
            closedPoll = True


        if closedPoll and not self.emoji.name == '❔':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            self.settingsEmbed.set_footer(text = "You can dismiss this message now")
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            return

        #* If button is lock
        if self.emoji.name == '🔐':
            isLocked_str = ":lock:" if not self.currentPoll.isLocked else ":unlock:"
            self.currentPoll.isLocked = True if not self.currentPoll.isLocked else False

            self.label = "Unlock" if isLocked_bool else "Lock"
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = isLocked_str)
            self.pollEmbed.set_field_at(2, name = "Poll is", value = isLocked_str)
            await self.pollMessage.edit(embed = self.pollEmbed)

            #* Locked Repeat logic
            for button in self.view.children[1:]:
                if isLocked_bool and str(button.emoji) == '🔁':
                    button.disabled = True
                    button.style = discord.ButtonStyle.danger
                elif str(button.emoji) == '🔁':
                    button.disabled = False
                    button.style = discord.ButtonStyle.success

            await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
            return

        #* If button is detective
        if self.emoji.name == '🕵️‍♂️':
            if self.currentPoll.isAnon:
                self.settingsEmbed.set_field_at(0, name = "Results are now", value = ":sunny: Shown with names")
                self.pollEmbed.set_author(name = "Results are shown with names", icon_url = "")
                await self.pollMessage.edit(embed = self.pollEmbed)
                self.currentPoll.isAnon = False
            else:
                self.settingsEmbed.set_field_at(0, name = "Results are now", value = ":detective: Anonymous")
                self.pollEmbed.set_author(name = "Results are Anonymous")
                await self.pollMessage.edit(embed = self.pollEmbed)
                self.currentPoll.isAnon = True
            self.currentPoll.pollEmbed = self.pollEmbed
            await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
            return

        #* If button is timelimit
        if self.emoji.name == '⌛':
            pollStarted = self.pollEmbed.timestamp
            view = Confirm(self.ctx)
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

                self.currentPoll.pollEmbed = self.pollEmbed

                pollView = Poll(self.currentPoll)
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")
            else:
                self.settingsEmbed.title = "Canceled Menu"
                self.settingsEmbed.description = "You can dismiss this message now"
                await interaction.followup.send(embed = self.settingsEmbed, ephemeral=True)

                pollView = Poll(self.currentPoll)
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")
            return

        #* If button is print
        if self.emoji.name == '🖨':
            if currPoll:
                results = []
                for key in currPoll:
                        member = self.ctx.guild.get_member(int(key))
                        results.append(f"[{member.display_name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") has voted")
                embed = discord.Embed(title = "Here's a list of people who have voted so far!", description = "\n".join(results), color = randomHexGen())
                await interaction.response.edit_message(embed = embed)
            else:
                embed = discord.Embed(title = "No one has voted yet!", color = randomHexGen())
                await interaction.response.edit_message(embed = embed)


        #* If button is edit
        if self.emoji.name == '➕':
            await interaction.response.defer()
            view = Confirm(self.ctx)
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

            emojiList = self.currentPoll.emojiList[:-1] + makeList_removeSpaces(emojis)
            optionList = self.currentPoll.optionList[:-1] + makeList_removeSpaces(msg)
            if len(emojiList) > 24:
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

                self.pollEmbed.description = "React with the corresponding emote to cast a vote. \n\n" + pairedString
                self.currentPoll.pollEmbed = self.pollEmbed #update description

                self.currentPoll.emojiList = emojiList + ['<a:settings:845834409869180938>']
                self.currentPoll.optionList = optionList + ['Settings']
                pollView = Poll(self.currentPoll)
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

                pollView = Poll(self.currentPoll)
                try:
                    pollView.message = await self.ctx.send(embed = self.pollEmbed, view = pollView)
                except Exception as e:
                    print(e)
                    return await self.ctx.send("Something went wrong!")
            return


        #* If button is cancel
        if str(self.emoji) == '<:cancel:851278899270909993>':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            self.settingsEmbed.set_footer(text = "You can dismiss this message now")
            try:
                resultsEmbed = await self.clipboardBot.bot.get_command('createResultsEmbed')(self.currentPoll)
            except Exception:
                print(traceback.format_exc())
                errorFile = open("data\error.txt","a")
                errorFile.write(traceback.format_exc())
                errorFile.close()
                return
            await self.pollMessage.edit(embed = resultsEmbed, view = None)
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            return

        #* Buttons non-authors can click on
        if str(interaction.user.id) in currPoll:
            if self.emoji.name == '❔':
                self.settingsEmbed.set_field_at(0, name = "Your vote is:", value = str(currPoll.get(str(interaction.user.id))))
                await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
                return
            if self.emoji.name == '🔁' and isLocked_bool:
                del currPoll[str(interaction.user.id)]
                writetoFile(currPoll, "storedPolls")
                self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = len(currPoll))
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

#* Settings View Class
class Settings(discord.ui.View):
    children: List[SettingsButton]
    def __init__(self, currentPoll, currentSettings):
        super().__init__()
        if currentSettings.isAuthor:
            settings = ['\U00002795', '\U00002754', '\U0001f501', '<:cancel:851278899270909993>']
            self.add_item(SelectMenu(currentPoll, currentSettings))
        else: settings = ['\U00002754', '\U0001f501', '\U0001f5a8']

        #* Adding Buttons
        for emoji in settings:
            button = SettingsButton(emoji, currentPoll, currentSettings)
            if str(button.emoji) == '<:cancel:851278899270909993>':
                button.style = discord.ButtonStyle.danger #turn red
            if str(button.emoji) == '\U00002795': #edit poll
                button.style = discord.ButtonStyle.primary #turn blurple
            if currentPoll.isLocked and str(button.emoji) == '\U0001f501': #If locked and button refresh
                button.disabled = True #disable
                button.style = discord.ButtonStyle.danger #turn red
            elif str(button.emoji) == '\U0001f501': #if unlocked and refresh
                button.style = discord.ButtonStyle.success #turn green
            self.add_item(button)


#* SelectMenu View
class SelectMenu(discord.ui.Select):
    def __init__(self, currentPoll, currentSettings):
        self.timeOption = discord.SelectOption(label="Timelimit", emoji="⌛")
        self.lockedOption = discord.SelectOption(label="Locked", emoji="🔐")
        self.anonOption = discord.SelectOption(label="Anonymity", emoji="🕵️‍♂️")
        self.printOption = discord.SelectOption(label="Print Who Voted", emoji="🖨")

        super().__init__(placeholder = "What would you like to modify?",
                         options=[self.timeOption, self.lockedOption, self.anonOption, self.printOption])

        self.timeButton = SettingsButton("⌛", currentPoll, currentSettings)
        self.lockedButton = SettingsButton("🔐", currentPoll, currentSettings)
        self.anonButton = SettingsButton("🕵️‍♂️", currentPoll, currentSettings)
        self.printButton = SettingsButton("🖨", currentPoll, currentSettings)

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

#* Setting up Cog
class voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("voting is Ready")

    @commands.group(aliases = ["poll", "p"])
    async def vote(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}poll create`")

    #* poll help menu
    @vote.command()
    async def help(self, ctx):
        await ctx.send(f"Use the command `{ctx.prefix}poll create` or \n`{ctx.prefix}poll create <Title>` to get started!")

#* ------------   Create Poll   ------------
    @vote.command(aliases = ["create", "start", "new", "c", "m", "s"])
    async def make(self, ctx, *, title = None):
        member = ctx.guild.get_member(ctx.author.id)
        embed = discord.Embed(description="")
        embed.set_author(name = ctx.author)

    #* Setting up the variables for the embed
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
        else: # need to fix what happens when no title is given
            entirePoll = title
            title = re.search(r"\A.*", entirePoll).group()
            msg = "\n".join(re.findall(r"[\w\s()'-]+$", entirePoll, re.MULTILINE)[1:])
            emojis = "\n".join(re.findall(r"^[^*]{1,2}(?!\w)", entirePoll, re.MULTILINE))

        emojiList = makeList_removeSpaces(emojis)
        optionList = makeList_removeSpaces(msg)

        if len(emojiList) > 25:
            return await ctx.send("Polls may only have up to 24 options. Try making the Poll again.")
        if len(emojiList) != len(optionList):
            return await ctx.send("You have an unmatched number of options and emojis. Try making the Poll again.")

    #* Forming the embed
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

        embed.set_author(name = "Results are shown with names")
        #* Footer
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


        try:
            fullEmojiList = emojiList + ['<a:settings:845834409869180938>']
            fullOptionList = optionList + ["Settings"]

            currentPoll = PollClass(ctx, self, embed, fullEmojiList, fullOptionList)

            pollView = Poll(currentPoll)
            pollView.message = await ctx.send(embed = embed, view = pollView)
        except Exception:
            print(traceback.format_exc())
            errorFile = open("data\error.txt","a")
            errorFile.write(traceback.format_exc())
            errorFile.close()
            return await ctx.send("One of your emojis is invalid! Try making the Poll again.")

    #* timeConvert
    @commands.command()
    async def timeConvert(self, ctx, *, inp: str):
        seconds = humantimeTranslator(inp)
        await ctx.send(seconds)

    #* Create Results Embed
    @commands.command()
    @commands.is_owner()
    async def createResultsEmbed(self, currentPoll):
        newPoll = readfromFile("storedPolls")
        embed = currentPoll.pollEmbed
        ctx = currentPoll.ctx
        pollClosingTime = embed.fields[1].value
        isAnon = currentPoll.isAnon

        results = []
        winners = []
        if newPoll:
            #* Winner Logic
            freqCounter = Counter(newPoll.values()) #Find the # votes for each emoji
            emoji, freq = zip(*freqCounter.most_common())
            the_rest = [emoji+" ➙ "+str(freq)+" votes" for emoji, freq in zip(emoji, freq)]
            maxNum = freq[0]
            winnerDict = {k: v for k, v in freqCounter.items() if v == maxNum} #Turn it into a dict to cycle through
            for key in winnerDict:
                winners.append(key) #Add winners with the most votes to winner list


            if isAnon:
                results = the_rest
            else:
                # Creating the large list of what everyone voted for
                for key, values in newPoll.items():
                        member = ctx.guild.get_member(int(key))
                        results.append(f"[{member.display_name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") voted {values}")

        #* Forming the embed
        embed.description = "\n".join(results) if results else "No one voted!"
        embed.clear_fields()

        if results:
            final_winner = ""
            if len(winners) == 1:
                final_winner = winners[0]
                embed.add_field(name = f"The winner (with {maxNum} votes)...", value = final_winner, inline = False)
            else:
                final_winner = random.choice(winners)
                embed.add_field(name = f"The winners (with {maxNum} votes)...", value = "\n".join(winners), inline = False)
                embed.add_field(name = "As there was a tie, one has been chosen at random from our winners", value = final_winner, inline = False)
            if not isAnon: embed.add_field(name = "The totals:", value = "\n".join(the_rest), inline = False)
            embed.title = f"Our winner is {final_winner}!!"

        embed.add_field(name = "Votes Recorded:", value = len(newPoll))
        embed.add_field(name = "Date Poll Started:", value = f"<t:{int(embed.timestamp.timestamp())}:f>")
        embed.add_field(name = "Date Poll Closed:", value = pollClosingTime)

        return embed


    #* Vote example command
    @vote.command()
    async def example(self, ctx):
        await ctx.guild.get_member(ctx.author.id).send("https://imgur.com/a/wq6swYo")

    @vote.command()
    @commands.is_owner()
    async def print(self, ctx):
        newPoll = readfromFile("storedPolls")
        results = []
        for key, values in newPoll.items():
                member = ctx.guild.get_member(int(key))
                results.append(f"[{member}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") voted {values}")
        privateEmbed = discord.Embed(title = "Here are the Results!", description = "\n".join(results), color = randomHexGen())
        await ctx.guild.get_member(ctx.bot.owner_id).send(embed = privateEmbed)
        return privateEmbed

    #* Insert dictionary
    @vote.command()
    @commands.is_owner()
    async def insertPoll(self, ctx, *, inp : str):
        newPoll = json.loads(inp.replace("'", "\""))
        writetoFile(newPoll, "storedPolls")
        await ctx.send("Dictionary inserted")

    #* Clear dictionary
    @vote.command()
    @commands.is_owner()
    async def clear(self, ctx):
        newPoll = readfromFile("storedPolls")
        newPoll.clear()
        writetoFile(newPoll, "storedPolls")
        await ctx.send("Successfully cleared poll!")

    #* Make a new Dictionary
    @vote.command()
    @commands.is_owner()
    async def saveReset(self, ctx):
        timestamp = datetime.today().strftime("%Y-%m-%d")
        pollName = f"storedPolls-{timestamp}"
        oldPoll = readfromFile("storedPolls")

        writetoFile(oldPoll, pollName)

        oldPoll.clear()
        writetoFile(oldPoll, "storedPolls")
        await ctx.send("Successfully reset poll!")

    #* Help with Admin Commands
    @commands.command(aliases = ["@help"])
    @commands.is_owner()
    async def adminHelp(self, ctx):
        await ctx.send("""```insertPoll <string input formatted json>
        clear
        saveReset
        timeConvert
        list @view
        ```""")

    #* checkVotes
    @commands.command(aliases = ["votecheck", "vc", "checkvote", "cv", "votescheck", "checkVote", "voteCheck"])
    @commands.is_owner()
    async def checkVotes(self, ctx, *, inp=None):
        if inp:
            today = datetime.now()
            lastday = date(today.year, today.month + 1, 1) - timedelta(days=1)
            daysLeft = lastday.day - today.day

            votesNeeded = int(inp.split(" ")[1]) - int(inp.split(" ")[0])
            await ctx.send(round(votesNeeded/daysLeft, 2))

        else:
            await ctx.send(f"`{ctx.prefix}checkVotes <# of votes so far> <total votes needed>`")

async def setup(bot):
    await bot.add_cog(voting(bot))
