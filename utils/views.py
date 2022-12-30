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

class EmbedPageView(discord.ui.View):
    def __init__(self, eList, pagenum, totpage):
        super().__init__(timeout=20)
        self.eList = eList
        self.pagenum = pagenum
        self.totpage = totpage

        if totpage > 1:
                backButton = EmbedPageButton("⇽ Back", discord.ButtonStyle.gray)
                nextButton = EmbedPageButton("⇾ Next", discord.ButtonStyle.blurple)
                if pagenum == 0:
                    backButton.disabled = True
                if pagenum == totpage - 1:
                    nextButton.disabled = True
                self.add_item(backButton)
                self.add_item(nextButton)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
        # await self.message.edit(view=None)

class EmbedPageButton(discord.ui.Button):
    def __init__(self, label, style):
        super().__init__(label = label, style = style, row = 4)

    async def callback(self, interaction:discord.Interaction):
        pagenum = self.view.pagenum
        if self.label == "⇽ Back":
            pagenum -= 1
        else:
            pagenum += 1
        await interaction.response.edit_message(embed=self.view.eList[pagenum], view=EmbedPageView(self.view.eList, pagenum, self.view.totpage))
