import discord
from discord.ext import commands, menus
from cogs.voting import createResultsEmbed
from main import randomHexGen

from typing import List

class menusUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("menusUtil is Ready")

#➥ Setting up a Confirmation Menu
class Confirm(discord.ui.View):    
    def __init__(self):
        super().__init__()
        self.value = None     
        
    @discord.ui.button(emoji="<:confirm:851278899832684564>", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()
        
    @discord.ui.button(emoji="<:cancel:851278899270909993>", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()
##
        
#➥ Setting up Viewing Notes Menu
class ViewNotes(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=9)
    
    async def format_page(self, menu, entries): 
        embed = discord.Embed(
            title = "Your Saved Notes",
            description = "Enter a number to view your selected note",
            color = randomHexGen()
        )
        embed.set_footer(text = f'\nPage {menu.current_page + 1}/{self.get_max_pages()}' + " | React with ❌ to cancel option selection")
        for entry in entries:
            embed.add_field(name = entry.option + " " + entry.title, value = entry.tag)        
        
        return embed
##
        
#➥ Setting up Deleting Notes Menu
class DeleteNotes(menus.MenuPages):
    def __init__(self, source):
        super().__init__(source = source, timeout = 60, delete_message_after=True)
        
    async def finalize(self, timed_out):
        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass
        
    @menus.button('<:cancel:851278899270909993>', position=menus.Last(0)) 
    async def on_cancel(self, payload):
        self.stop()
##

#➥ Setting up Menu Page Source
class EmbedFormatSource(menus.ListPageSource):
    def __init__(self, entries, per_page):
        super().__init__(entries, per_page=per_page)
            
    async def format_page(self, menu, entries): 
            embed = discord.Embed(
                title = "Selected Note(s) to be Deleted: \n" + entries[0].title,
                description = "Enter a number to delete selected note",
                color = randomHexGen()
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/519350010706395157/850574601623961640/full_cross.png")
            embed.set_footer(text = f'\nPage {menu.current_page + 1}/{self.get_max_pages()}' + " | React with ❌ to cancel option selection")
            for entry in entries:
                embed.add_field(name = entry.option + "\n__" + entry.tag + "__", value = entry.content)        
            return embed
##

#➥ Poll View Class
class Poll(discord.ui.View):    
    def __init__(self, ctx, pollEmojiList, optionList, dictionary, embed):
        super().__init__(timeout = 15)
        self.optionList = optionList
        self.dictionary = dictionary
        self.embed = embed
        self.ctx = ctx
        
        for emoji, label in zip(pollEmojiList, optionList):
            self.add_item(PollButton(ctx, emoji, label, dictionary, embed))
    
    async def on_timeout(self):
        await self.message.edit(embed = createResultsEmbed(self.ctx, self.dictionary, self.embed), view = None)
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
            content = ":pencil2: ➙ Edit the Poll \n:grey_question: ➙ Check Your Vote \n:repeat: ➙ Clear your vote\n:closed_lock_with_key: ➙ Toggle if voters are allowed to clear their vote \n:alarm_clock: ➙ Change the timelimit (Default is 3 Days)\n:detective: ➙ Toggle result anonymity\n<:cancel:851278899270909993> ➙ Close the Poll & Show results"
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
        try:
            isLocked_bool = True if self.pollEmbed.fields[2].value == ":unlock:" else False
        except IndexError:
            closedPoll = True
        
        if closedPoll and not self.emoji.name == '❔':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            await interaction.response.edit_message(embed = self.settingsEmbed, view = None)
            return
        
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
        
        if str(self.emoji) == '<:cancel:851278899270909993>':
            self.settingsEmbed.set_field_at(0, name = "The poll is now", value = '<:cancel:851278899270909993> Closed')
            await self.pollMessage.edit(embed = createResultsEmbed(self.ctx, self.dictionary, self.pollEmbed), view = None)
            await interaction.edit(embed = self.settingsEmbed, view = None)
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
        self.timeOption = discord.SelectOption(label="Timelimit", emoji="⏰")
        self.lockedOption = discord.SelectOption(label="Locked", emoji="🔐")
        self.anonOption = discord.SelectOption(label="Anonymity", emoji="🕵️‍♂️")
        
        super().__init__(placeholder = "What would you like to modify?", 
                         options=[self.timeOption, self.lockedOption, self.anonOption])
        
        self.timeButton = SettingsButton(ctx, "⏰", dictionary, pollEmbed, settingsEmbed, pollMessage)
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




def setup(bot):
    bot.add_cog(menusUtil(bot))