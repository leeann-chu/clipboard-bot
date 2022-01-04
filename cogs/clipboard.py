from typing import List
import discord
import re

from main import randomHexGen, db
from utils.models import Lists, Tasks, recreate
from utils.views import Cancel, Confirm
from discord.ext import commands

def formatContent(data):
    items = (re.sub('\n- |\n-|\n• |\n•', '\n', data))
    itemList = items.split("\n")
    spaceless = [{s.strip()} for s in itemList]
    return spaceless

class ListView(discord.ui.View):
    def __init__(self, ctx, db, titleList, numList):
        super().__init__()
        self.ctx = ctx
        self.db = db
        
        for emoji, title in zip(numList, titleList):
            button = ListButton(emoji, title)
            self.add_item(button)
            
    @discord.ui.button(emoji = "<:cancel:851278899270909993>", label="Exit", style=discord.ButtonStyle.red, custom_id = "cancel", row=4)
    async def cancel(self, button: discord.ui.button, interaction: discord.Interaction):
        await self.message.delete()
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("No.", ephemeral= True)
        else:
            selected = list(interaction.data.values())[0]
            if selected == "done":
                await interaction.response.edit_message(view = None)
        return await super().interaction_check(interaction)        

class ListButton(discord.ui.Button['ListView']):
    def __init__(self, emoji, title):
        super().__init__(emoji = emoji, label = title)
        
    async def callback(self, interaction: discord.Interaction):   
        menu = ScopeSelect(self)
        done = discord.ui.Button(emoji = "<:confirm:851278899832684564>", label="Close Buttons", style=discord.ButtonStyle.green, custom_id = "done", row=4)
        childrenCID = []
 
        for child in self.view.children:
            try:
                childrenCID.append(child.custom_id)
            except: pass

        if done.custom_id not in childrenCID:
            self.view.add_item(done)
        if menu.custom_id not in childrenCID:
            self.view.add_item(menu)
            
        selList = self.view.db.query(Lists).filter_by(title = self.label).first()     
        await interaction.response.edit_message(embed = view(selList), view=self.view)
        
class ListSettings(discord.ui.View):
    def __init__(self, ogView):
        super().__init__()
        self.add_item(ScopeSelect(ogView))
        
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
    def __init__(self, ogView):
        super().__init__()
        self.ogView = ogView
        self.add_item(ScopeSelect(ogView))
        
    @discord.ui.button(emoji="<:check:926281518266073088>", label="Change Task Status", style=discord.ButtonStyle.green)
    async def status(self, button: discord.ui.button, interaction: discord.Interaction):
        print(self.view.message.embeds)
        # await interaction.response.edit_message(content="this changed", embed = self.ogView.message.embeds[0])
        
    @discord.ui.button(emoji="✏", label="Rename Task", style=discord.ButtonStyle.gray)
    async def edit(self, button: discord.ui.button, interaction: discord.Interaction):
        print("rename task")
        
    @discord.ui.button(emoji="➕", label="Add Task", style=discord.ButtonStyle.primary)
    async def add(self, button: discord.ui.button, interaction: discord.Interaction):
        print("add tasks")
        
    @discord.ui.button(emoji="<:cross:926283850882088990>", label="Remove Task", style=discord.ButtonStyle.red)
    async def delete(self, button: discord.ui.button, interaction: discord.Interaction):
        print("remove task")

class CompleteView(discord.ui.View):
    def __init__(self, ctx, db, title):
        super().__init__()
        self.ctx = ctx
        self.title = title
        self.db = db
        selList = self.db.query(Lists).filter_by(title = title).first()
        for task in selList.rel_tasks:
            self.add_item(CompleteButtons(task.status, task.taskItem))
        
class CompleteButtons(discord.ui.Button):
    def __init__(self, emoji, label):
        super().__init__(emoji = emoji, label = label)
        
    async def callback(self, interaction: discord.Interaction):  
        selTask = self.view.db.query(Tasks).filter_by(taskItem = self.label)
        selTask.status = "<:check:926281518266073088>"
        self.view.db.commit()
        await interaction.response.edit_message(embed = view(selTask, True))

class ScopeSelect(discord.ui.Select):
    def __init__(self, ogView):
        self.listOption = discord.SelectOption(label="List Settings", emoji="<:list:927096692069789696>")
        self.taskOption = discord.SelectOption(label="Task Settings", emoji="<:notdone:926280852856504370>")
        self.backOption = discord.SelectOption(label="Go Back", emoji="◀️")
        
        self.oldView = ogView
        
        super().__init__(placeholder = "Select between List and Task Settings",
                         options = [self.listOption, self.taskOption, self.backOption], custom_id="menu")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "List Settings":
            view = ListSettings(self.oldView)
        elif self.values[0] == "Task Settings":
            view = TaskSettings(self.oldView)
        else:
            view = self.oldView
        return await interaction.response.edit_message(view = view)     

#* ------- Setting up Cog -------
class clipboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = db
        
    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("clipboard is Ready")
        
    @commands.group(aliases = ["checklist", "clipboard", "l", "list", "lists", "task"])
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
            self.db.add(_list)
            for task in taskList:
                newTask = Tasks(listID = _list.id, taskItem = task)
                self.db.add(newTask)
                _list.rel_tasks.append(newTask)

            self.db.commit()
            return await confirmationEmbed.edit("Saved to Database!", embed = embed, view = None)
        else:
            embed.description = "List canceled!"
            return await confirmationEmbed.edit(embed = embed, view = None, delete_after = 5)
##

#* Select your lists
    @_list.command(aliases = ["b", "view"])
    async def browse(self, ctx, *, filterOption=None):
        member = ctx.guild.get_member(ctx.author.id)
    
        if filterOption is None:
            allLists = self.db.query(Lists).filter_by(author = str(ctx.author.id)).all()
        else: # given argument search for
            allLists = self.db.query(Lists).filter(Lists.title.like(f'{filterOption}%')).all()
            if not allLists:
                allLists = self.db.query(Lists).filter(Lists.author_name.like(f'{filterOption}%')).all()

        if len(allLists) > 1:
            numList = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
            titleList = [_list.title for _list in allLists]
            numList = numList[:len(titleList)]
        elif len(allLists) == 1:
            return await ctx.send(embed = view(allLists[0]))
        else:
            return await ctx.send(f"List(s) not found! Create a list using `{ctx.prefix}list create`")
        viewListObject = ListView(ctx, self.db, titleList, numList)
        viewListObject.message = await ctx.send(f"> Choose a list to view! • [{member}]", view = viewListObject)
##
#* Mark Tasks as complete
    @_list.command(aliases = ["checkoff"])
    async def complete(self, ctx, *, title: str):
        selList = self.db.query(Lists).filter_by(title = title).first()
        await ctx.send(embed = view(selList, True), view = CompleteView(ctx, self.db, title))
    
    @complete.error
    async def _list_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'title':
                await ctx.send("You must specify which List's tasks you would like to mark complete")
##      

#* View one list
    @commands.command(aliases = ["view", "v"]) # command that is not nested in the Note Group
    async def open(self, ctx, *, title=None):
        if title is None:
            await self._list.get_command('browse')(ctx)

        else:
            selList = self.db.query(Lists).filter_by(title = title).first()
            await ctx.send(embed = view(selList))

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

def view(selList, numbered=None):
    if selList:
        if numbered:
            taskList = [(f"{task[1].status} {format(task[0], '>3')}. {task[1].taskItem}") for task in enumerate(selList.rel_tasks, start = 1)]
        else:
            taskList = [(f"{task[1].status} {task[1].taskItem}") for task in enumerate(selList.rel_tasks, start = 1)]
        embed = discord.Embed(
            title = selList.title,
            description = f"\n".join(taskList),
            color = 0x2F3136,
            timestamp = selList.created
        )
        embed.set_footer(text = f"Owned by {selList.author_name}")
    else:
        embed = discord.Embed(
            title = f"No lists were found with that name!"
        )      
    return embed

def setup(bot):
    bot.add_cog(clipboard(bot))