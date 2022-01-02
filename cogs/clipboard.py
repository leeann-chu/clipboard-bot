from typing import List
import discord
import re

from main import randomHexGen
from utils.models import Session, Lists, Tasks, recreate
from utils.views import Cancel, Confirm
from discord.ext import commands

def formatContent(data):
    items = (re.sub('\n- |\n-|\n• |\n•', '\n', data))
    itemList = items.split("\n")
    spaceless = [{s.strip()} for s in itemList]
    return spaceless

class ListView(discord.ui.View):
    def __init__(self, titleList, numList, nextStep):
        super().__init__()
        self.nextStep = nextStep
        
        for emoji, title in zip(numList, titleList):
            button = ListButton(emoji, title)
            self.add_item(button)
        
        cancelButton = discord.ui.Button(emoji = "<:cancel:851278899270909993>", label="Cancel", style=discord.ButtonStyle.red, custom_id = "cancel", row=4)
        self.add_item(cancelButton)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        selected = list(interaction.data.values())[0]
        if selected == "cancel":
            await self.message.delete()
        elif selected == "done":
            await interaction.response.edit_message(view = None)
            
        return await super().interaction_check(interaction)

class ListButton(discord.ui.Button['ListView']):
    def __init__(self, emoji, title):
        super().__init__(style=discord.ButtonStyle.gray, emoji = emoji, label = title)
        
    async def callback(self, interaction: discord.Interaction):
        done = discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", 
                                 style=discord.ButtonStyle.green, custom_id="done", row=4)
        
        if done not in self.view.children:
            print("done is not in children")
            self.view.add_item(done)
        else:
            print("done is in children")
        
        await interaction.response.edit_message(embed = view(self.label), view=self.view)
        
class ListSettings(discord.ui.View):
    def __init__(self):
        super().__init__()
        # self.add_item(ScopeSelect(self.view))
        
    @discord.ui.button(emoji="✏", label="Rename List", style=discord.ButtonStyle.gray)
    async def edit(self, button: discord.ui.button, interaction: discord.Interaction):
        print("rename list")
        
    @discord.ui.button(emoji="🙈", label="Hide List", style=discord.ButtonStyle.gray)
    async def hide(self, button: discord.ui.button, interaction: discord.Interaction):
        print("hide list")
        
    @discord.ui.button(emoji="<:trash:926991605615960064>", label="Delete List", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.button, interaction: discord.Interaction):
        print("delete list")
        
class TaskSettings(discord.ui.View):
    def __init__(self):
        super().__init__()
        # self.add_item(ScopeSelect(self.view))
        
    @discord.ui.button(emoji="✏", label="Rename Task", style=discord.ButtonStyle.gray)
    async def edit(self, button: discord.ui.button, interaction: discord.Interaction):
        print("rename task")
        
    @discord.ui.button(emoji="➕", label="Add Task", style=discord.ButtonStyle.primary)
    async def add(self, button: discord.ui.button, interaction: discord.Interaction):
        print("add tasks")
        
    @discord.ui.button(emoji="<:cross:926283850882088990>", label="Remove Task", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.button, interaction: discord.Interaction):
        print("remove task")

class ScopeSelect(discord.ui.Select):
    def __init__(self, listView):
        self.listOption = discord.SelectOption(label="List Settings", emoji="<:list:927096692069789696>")
        self.taskOption = discord.SelectOption(label="Task Settings", emoji="<:notdone:926280852856504370>")
        self.backOption = discord.SelectOption(label="Go Back", emoji="◀️")
        
        self.oldView = listView
        
        super().__init__(placeholder = "Select between List and Task Settings",
                         options = [self.listOption, self.taskOption, self.backOption])

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "List Settings":
            view = ListSettings()
        elif self.values[0] == "Task Settings":
            view = TaskSettings()
        else:
            view = self.oldView
        return await interaction.response.edit_message(view = view)     

#* Setting up Cog   
class clipboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("clipboard is Ready")
        
    @commands.group(aliases = ["checklist", "clipboard", "l", "list", "lists"])
    async def _list(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Please specify what you'd like to do. \nEx: `{ctx.prefix}list create` \nSee `{ctx.prefix}list help` for a list of examples!")

    @commands.group(aliases = ["n", "notes"])
    async def note(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Note subcommands are wip, use `{ctx.prefix}list create` to create lists instead")
##
    
#* -------    List Creation   -------
    @_list.command(aliases = ["create", "new", "c", "m"])
    async def make(self, ctx, *, title=None):
        member = ctx.guild.get_member(ctx.author.id)
        try: pfp = member.avatar.url
        except: pfp = None

        await ctx.trigger_typing()
        embed = discord.Embed (
            title = "Checklist Creation",
            description = "",
            color = randomHexGen()
        )
        view = Cancel()
    #* Checklist Creation Embed
        if title is None:
            embed.description = "What would you like the **Title**/**Category** of your checklist to be?"
            embed.set_footer(text=f"{member}'s list | Title cannot exceed 200 characters") 
            titlePrompt = await ctx.send(f"> This question will time out in `3 minutes` • [{member}]", embed = embed, view = view)
            title = await self.bot.get_command('multi_wait')(ctx, view, 180)
            if len(title) > 200:
                title = False
                return await ctx.send("Title cannot exceed 200 characters, try again")
            if not title:
                embed.description = f"List Creation canceled."
                embed.remove_footer()
                return await titlePrompt.edit(embed = embed, view = None, delete_after = 5)
            await titlePrompt.delete()

        if "\n" not in title:
            embed.description = "Enter the tasks you wish to complete seperated by *new lines*"
            embed.set_footer(text=f"{member}'s list")
            tasksPrompt = await ctx.send(f"> This question will time out in `6 minutes` • [{member}]", embed = embed, view = view)
            taskString = await self.bot.get_command('multi_wait')(ctx, view, 400)
            taskList = (re.sub('\n- |\n-|\n• |\n•', '\n', taskString)).split("\n")
            if not taskString:
                embed.description = f"List Creation canceled."
                embed.remove_footer()
                return await tasksPrompt.edit(embed = embed, view = None, delete_after = 5)
            await tasksPrompt.delete()

        else:
            entireList = title
            title = re.match(r"\A.*", entireList).group()
            taskList = (re.sub('\n- |\n-|\n• |\n•', '\n', entireList)).split("\n")[1:] #turn into a list
    ##
        taskString = "\n<:notdone:926280852856504370> ".join(['', *taskList]) #Turn into a string
    #* Confirmation Embed
        embed = discord.Embed (
            title = f"{title}",
            description = taskString, 
            color = 0x2F3136
        )
        embed.set_footer(text=f"Owned by {member}", icon_url=pfp if pfp else '')
        view = Confirm()
        confirmationEmbed = await ctx.send("Does this look correct?", embed = embed, view=view)
    ##
        await view.wait()
        if view.value is None:
            embed.description = "Confirmation menu timed out!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 3)
        elif view.value:
            _list = Lists(title = title, author = str(ctx.author.id), author_name = member.name)
            s = Session()
            s.add(_list)
            for task in taskList:
                newTask = Tasks(listID = _list.id, taskItem = task)
                s.add(newTask)
                _list.rel_tasks.append(newTask)

            s.commit()
            s.close()
            return await confirmationEmbed.edit("Saved to Database!", embed = embed, view = None)
        else:
            embed.description = "List canceled!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 5)
##

#* Select your lists
    @_list.command(aliases = ["b", "view"])
    async def browse(self, ctx, *, filter=None):
        s = Session()
        if filter is None:
            allLists = s.query(Lists).filter_by(author = str(ctx.author.id)).all()
            member = ctx.guild.get_member(ctx.author.id)
  
        s.close()

        if len(allLists) > 1:
            numList = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
            titleList = [_list.title for _list in allLists]
            numList = numList[:len(titleList)]
        elif len(allLists) == 1:
            return await ctx.send(embed = view(allLists[0].title))
        else:
            return await ctx.send(f"No lists found for this user! Create a list using `{ctx.prefix}list create`")
        viewListObject = ListView(titleList, numList, False)
        viewListObject.message = await ctx.send(f"> Choose a list to view! • [{member}]", view = viewListObject)
##

#* View one list
    @commands.command(aliases = ["view", "v"])
    async def open(self, ctx, *, title=None):
        if title is None:
            await self._list.get_command('browse')(ctx)

        else:
            await ctx.send(embed = view(title))

##

#* Other Commands
    @_list.command()
    async def recreate(self, ctx):
        recreate()
        await ctx.send("Database recreated")

    @_list.command()
    async def emoji(self,ctx):
        embed = discord.Embed (
            title = type(ctx.author.id),
            description = 
            """<:wip:926281721224265728> Harass Nathaniel
            <:notdone:926280852856504370> Work on Copper pot
            <:check:926281518266073088> Buy Dildos
            """,
            # description = "",
            color = 0x2F3136
        )

        await ctx.send(embed = embed)
##

def setup(bot):
    bot.add_cog(clipboard(bot))

def view(title):
    s = Session()
    selList = s.query(Lists).filter_by(title = title).first()
    taskList = [f"{task.status} {task.taskItem}" for task in selList.rel_tasks]
    s.close()
    
    embed = discord.Embed(
        title = selList.title,
        description = "\n".join(taskList),
        color = 0x2F3136,
        timestamp = selList.created
    )
    embed.set_footer(text = f"Owned by {selList.author_name}")

    return embed