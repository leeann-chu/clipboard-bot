import json
import discord

class PollClass:
    def __init__(self, ctx, clipboardBot, pollEmbed, emojiList, optionList, isAnon = False, isLocked = False, newPoll = {}):
        self.ctx = ctx
        self.clipboardBot = clipboardBot
        self.emojiList = emojiList
        self.optionList = optionList
        self.pollEmbed = pollEmbed
        self.isAnon = isAnon
        self.isLocked = isLocked
        self.newPoll = newPoll

class SettingsClass:
    def __init__(self, settingsEmbed, message, isAuthor):
        self.settingsEmbed = settingsEmbed
        self.message = message
        self.isAuthor = isAuthor

def writetoFile(data, file):
    with open(f'data/{file}.json', 'w') as f:
        json.dump(data, f,  indent=4)
def readfromFile(file):
    with open(f'data/{file}.json', 'r') as f:
        data = json.load(f)
    return data

#➥ Setting up a Confirmation Menu
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(emoji="<:confirm:851278899832684564>", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(emoji="<:cancel:851278899270909993>", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = False
        self.stop()
##

class Cancel(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        
    @discord.ui.button(emoji="<:cancel:851278899270909993>", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = False
        self.stop()
