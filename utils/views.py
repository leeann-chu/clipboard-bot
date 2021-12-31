import discord

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
