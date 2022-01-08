import discord

#➥ Setting up a Confirmation Menu
class Confirm(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.value = None
        self.ctx = ctx
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)  
            return False
        else:
            return await super().interaction_check(interaction)

    @discord.ui.button(emoji="<:confirm:851278899832684564>", label = "Yes", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(emoji="<:cancel:851278899270909993>", label = "No", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = False
        self.stop()
##

class Cancel(discord.ui.View):
    def __init__(self, ctx):
        super().__init__()
        self.value = None
        self.ctx = ctx
        
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This is not your menu to navigate.", ephemeral= True)  
            return False
        else:
            return await super().interaction_check(interaction)
        
    @discord.ui.button(emoji="<:cancel:851278899270909993>", label = "Exit", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.button, interaction: discord.Interaction):
        self.value = False
        self.stop()
