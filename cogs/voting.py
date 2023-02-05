import random
import json
import re
from datetime import datetime, timedelta, timezone, date
from collections import defaultdict, Counter
import discord, traceback
from discord.ext import commands
from myutils.poll_class import PollClass, SettingsClass, writetoFile, readfromFile
from typing import List
from main import randomHexGen

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
        num_seconds = int(parts.group(1)) * mult_items[parts.group(2)] + humantimeTranslator(re.sub(r'^(\d+)([^\d]*)', '', s.lower()))
        return f"{num_seconds} seconds"
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
        super().__init__(timeout = 86400) # 86400 for a day
        self.currentPoll = currentPoll

        for emoji, label in zip(currentPoll.emojiList, currentPoll.optionList):
            button = PollButton(currentPoll, emoji, label)
            if str(button.emoji) == '<a:settings:845834409869180938>':
                button.style = discord.ButtonStyle.primary
            self.add_item(button)

    async def on_timeout(self) -> None:
        resultsEmbed = await self.currentPoll.ctx.bot.get_command('createResultsEmbed')(self.currentPoll)
        await self.message.edit(embed = resultsEmbed, view = None)

#* Custom Button for Polls
class PollButton(discord.ui.Button['Poll']):
    def __init__(self, currentPoll, emoji, label):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji, label = label)
        self.ctx = currentPoll.ctx
        self.currentPoll = currentPoll
        self.clipboardBot = currentPoll.ctx.bot
        self.emoji = emoji
        self.pollEmbed = currentPoll.pollEmbed

    async def callback(self, interaction: discord.Interaction):
        currPoll = readfromFile("storedPolls")

    #* Settings Embed
        if self.ctx.author.id == interaction.user.id:
            content = ":grey_question: ➙ Check your vote \n:repeat: ➙ Clear your vote\n<:cancel:851278899270909993> ➙ Close the Poll \n\n:closed_lock_with_key: ➙ Toggle if voters are allowed to clear their vote \n:detective: ➙ Toggle anonymity\n:printer: ➙ See who has voted"
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
            return await interaction.response.send_message(embed = settingsEmbed, view = Settings(self.currentPoll, currentSettings), ephemeral = True)

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

            return await interaction.followup.send(embed = followup, view = Settings(self.currentPoll, currentSettings), ephemeral = True)
        # Already in Poll
        if str(interaction.user.id) in currPoll:
            followup = discord.Embed (title = "You have already voted!",
                                      description = "If you would like to see what you voted for try :grey_question:\nIf you would like to change your vote use :repeat:")
            return await interaction.response.send_message(embed = followup, view = Settings(self.currentPoll, currentSettings), ephemeral = True)

#* Custom Button for Settings
class SettingsButton(discord.ui.Button['Settings']):
    def __init__(self, emoji, currentPoll, currentSettings):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji)
        self.ctx = currentPoll.ctx
        self.clipboardBot = currentPoll.ctx.bot
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
            return await interaction.response.edit_message(embed = self.settingsEmbed, view = None)

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

            return await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)

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
            return await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)

        #* If button is print
        if self.emoji.name == '🖨':
            if currPoll:
                results = []
                for key in currPoll:
                    member = self.ctx.guild.get_member(int(key))
                    results.append(f"[{member.display_name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ \"{member.name}\") has voted")
                embed = discord.Embed(title = "Here's a list of people who have voted so far!", description = "\n".join(results), color = randomHexGen())
            else:
                embed = discord.Embed(title = "No one has voted yet!", color = randomHexGen())
            return await interaction.response.edit_message(embed = embed) # crucial to have a return here

        #* If button is cancel
        if str(self.emoji) == '<:cancel:851278899270909993>':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            self.settingsEmbed.set_footer(text = "You can dismiss this message now")
            try:
                resultsEmbed = await self.clipboardBot.get_command('createResultsEmbed')(self.currentPoll)
            except Exception:
                print(traceback.format_exc())
                return
            await self.pollMessage.edit(embed = resultsEmbed, view = None)
            return await interaction.response.edit_message(embed = self.settingsEmbed, view = None)

        #* Buttons non-authors can click on
        if str(interaction.user.id) in currPoll:
            if self.emoji.name == '❔':
                self.settingsEmbed.set_field_at(0, name = "Your vote is:", value = str(currPoll.get(str(interaction.user.id))))
                return await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
                
            if self.emoji.name == '🔁' and isLocked_bool:
                del currPoll[str(interaction.user.id)]
                writetoFile(currPoll, "storedPolls")
                self.pollEmbed.set_field_at(0, name = "Votes Recorded: ", value = len(currPoll))
                self.settingsEmbed.set_field_at(0, name = "You haven't voted yet!", value = "\u200b")
                await self.pollMessage.edit(embed = self.pollEmbed)
                return await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
                
            else:
                self.settingsEmbed.set_field_at(0, name = "Poll is :lock:", value = "You cannot change your vote")
                return await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)
        else:
            if self.emoji.name == '❔' or self.emoji.name == '🔁':
                self.settingsEmbed.set_field_at(0, name = "You haven't voted yet!", value = "\u200b")
                return await interaction.response.edit_message(embed = self.settingsEmbed, view = self.view)

#* Settings View Class
class Settings(discord.ui.View):
    children: List[SettingsButton]
    def __init__(self, currentPoll, currentSettings):
        super().__init__()
        if currentSettings.isAuthor: # ? , revote, print, cancel
            settings = ['\U00002754', '\U0001f501', '\U0001f5a8', '<:cancel:851278899270909993>']
            self.add_item(SelectMenu(currentPoll, currentSettings))
        else: settings = ['\U00002754', '\U0001f501', '\U0001f5a8'] # ?, revote, print

        #* Adding Buttons
        for emoji in settings:
            button = SettingsButton(emoji, currentPoll, currentSettings)
            if str(button.emoji) == '<:cancel:851278899270909993>':
                button.style = discord.ButtonStyle.danger #turn red
            if currentPoll.isLocked and str(button.emoji) == '\U0001f501': #If locked and button refresh
                button.disabled = True #disable
                button.style = discord.ButtonStyle.danger #turn red
            elif str(button.emoji) == '\U0001f501': #if unlocked and refresh
                button.style = discord.ButtonStyle.success #turn green
            self.add_item(button)

#* SelectMenu View
class SelectMenu(discord.ui.Select):
    def __init__(self, currentPoll, currentSettings):
        self.lockedOption = discord.SelectOption(label="Locked", emoji="🔐")
        self.anonOption = discord.SelectOption(label="Anonymity", emoji="🕵️‍♂️")

        super().__init__(placeholder = "What would you like to modify?",
                         options=[self.lockedOption, self.anonOption])

        self.lockedButton = SettingsButton("🔐", currentPoll, currentSettings)
        self.anonButton = SettingsButton("🕵️‍♂️", currentPoll, currentSettings)

    async def callback(self, interaction: discord.Interaction):
        self.options = [self.lockedOption, self.anonOption]

        if self.values[0] == "Locked": # select lock
            self.view.add_item(self.lockedButton)
            self.options.remove(self.lockedOption)
            try:
                self.view.remove_item(self.anonButton)
            except Exception: 
                print(traceback.format_exc())

        elif self.values[0] == "Anonymity": # select anonymous
            self.view.add_item(self.anonButton)
            self.options.remove(self.anonOption)
            try: 
                self.view.remove_item(self.lockedButton)
            except Exception:
                print(traceback.format_exc())

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
        oldPoll = readfromFile("storedPolls")
        if oldPoll: # commented out while debugging
            return await ctx.send("Last poll has not been reset, <@364536918362554368> reset the poll pls")

    #* Setting up the variables for the embed
        if title is None: 
            # do modal things
            print("title was none")

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
        pollClose = timestamp + timedelta(seconds =+ 86400) # 86400 is day
        embed.add_field(name = "Votes Recorded:", value = len(oldPoll))
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
        embed.set_footer(text = f"{random.choice(tips)}\n", icon_url = member.avatar.url)

        try:
            fullEmojiList = emojiList + ['<a:settings:845834409869180938>']
            fullOptionList = optionList + ["Settings"]

            currentPoll = PollClass(ctx, embed, fullEmojiList, fullOptionList)

            pollView = Poll(currentPoll)
            pollView.message = await ctx.send(embed = embed, view = pollView)
        except Exception:
            print(traceback.format_exc())
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
                    member = currentPoll.ctx.guild.get_member(int(key))
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
        embed.add_field(name = "Date Poll Closed:", value = f"<t:{int(discord.utils.utcnow().timestamp())}:f>")

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
        if oldPoll == {}:
            return await ctx.send("Poll has already been reset!")
        writetoFile(oldPoll, pollName)

        oldPoll.clear()
        writetoFile(oldPoll, "storedPolls")
        await ctx.send("Successfully reset poll!")

async def setup(bot):
    await bot.add_cog(voting(bot))
