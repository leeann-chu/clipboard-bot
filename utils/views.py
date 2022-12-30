import discord
from datetime import datetime

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
    def __init__(self, ctx, timeout=400):
        super().__init__(timeout=timeout)
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

## 

class EmbedPageView(discord.ui.View):
    def __init__(self, eList, pagenum):
        super().__init__(timeout=20)
        self.eList = eList
        self.pagenum = pagenum
        self.totpage = len(self.eList)

        self.children[0].disabled = True # back button should be disabled on init
    
    async def update_children(self, i: discord.Interaction):
        self.back.disabled = self.pagenum <= 0
        self.next.disabled = self.pagenum + 1 >= self.totpage

        await i.response.edit_message(embed=self.eList[self.pagenum], view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
    
    @discord.ui.button(label = "⇽ Back", style = discord.ButtonStyle.gray)
    async def back(self, i:  discord.Interaction, button: discord.ui.Button):
        self.pagenum -= 1
        await self.update_children(i)

    @discord.ui.button(label = "⇾ Next", style = discord.ButtonStyle.blurple)
    async def next(self, i:  discord.Interaction, button: discord.ui.Button):
        self.pagenum += 1
        await self.update_children(i)
