import discord
from datetime import datetime
from random import choice, shuffle, randint
from discord.ext import commands
from myutils.poll_class import writetoFile, readfromFile
from main import randomHexGen
import re

player_path = "corpse/listofplayers"
corpse_path = "corpse/corpse_links"
chief_executor = 364536918362554368
missing_perms = ["Fetch your maid outfit first", "Nice Try", "Not feeling up to it today", "Nop.", "That was very unbased of you"]

oldCorpses = ["https://discord.com/channels/370200859675721728/456508133913788436/519632182772367380",
            "https://discord.com/channels/370200859675721728/456508133913788436/520423673904234497",
            "https://discord.com/channels/370200859675721728/456508133913788436/511893556428931076",
            "https://discord.com/channels/370200859675721728/456508133913788436/511300834412331009",
            "https://discord.com/channels/370200859675721728/456508133913788436/502242294116646922",
            "https://discord.com/channels/370200859675721728/456508133913788436/464996344386551818"]

def passingTheCorpse(marked_as:str):
    checkList = readfromFile(player_path)
    # who is currently being marked
    hotSeat = list(checkList.keys())[checkList["HotSeat"]]
    # mark as {whatever}
    checkList[hotSeat] = marked_as

    # but if there is no next
    checkList["HotSeat"] = checkList["HotSeat"] + 1
    if (len(checkList) == checkList["HotSeat"]):
        writetoFile(checkList, player_path)
        return 0, "True"

    # move hotseat to the next 
    newHotSeat = list(checkList.keys())[checkList["HotSeat"]]
    checkList[newHotSeat] = "<:wip:926281721224265728>"
    writetoFile(checkList, player_path)
    return checkList["HotSeat"]-3, newHotSeat

def beginCorpseEmbed(bot):
    corpseRoster = readfromFile(player_path)

    # Init our checklist
    checkList = { "HotSeat": 1 }
    checkList.update({name: "<:notdone:926280852856504370>" for name in corpseRoster})

    # mark our first player as in progress
    checkList[corpseRoster[0]] = "<:wip:926281721224265728>"

    writetoFile(checkList, player_path) # now it is a dictionary

    embed = discord.Embed(
        title = "Let The Corpsing Commence!",
        description = "\n".join([ f"{i + 1}. {bot.get_user(user_id).name}" for i, user_id in enumerate(corpseRoster)]),
        color = randomHexGen(),
    )
    return embed, corpseRoster[0]

def corpseViewEmbed(bot, user_id: int = None, action_type: str = None):
    corpseRoster = readfromFile(player_path) # list right now
    printList = []
    if user_id:
        if action_type == "join":
            if user_id not in corpseRoster:
                corpseRoster.append(user_id)
                writetoFile(corpseRoster, player_path)
        elif action_type == "leave":
            if user_id in corpseRoster:
                corpseRoster.remove(user_id)
                writetoFile(corpseRoster, player_path)
        
        # else just viewing corpse
        printList = [bot.get_user(user_id).name for user_id in corpseRoster]

    embed = discord.Embed(
        title = "Corpse Roster",
        description = "\n".join(printList) if corpseRoster else "No one has joined this corpse!",
        color = randomHexGen(),
        url = choice(oldCorpses)
    )
    return embed

def shuffleViewEmbed(bot):
    corpseRoster = readfromFile(player_path)
    shuffle(corpseRoster)
    writetoFile(corpseRoster, player_path)
    printList = [bot.get_user(user_id).name for user_id in corpseRoster]
    embed = discord.Embed(
        title = "Shuffled Roster",
        description = "\n".join(printList) if corpseRoster else "No one has joined this corpse!",
        color = randomHexGen(),
    )
    return embed

# Corpse Join View
class CorpseView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=86400) # one day
        self.bot = bot

    # Add join, leave
    @discord.ui.button(label = "Join")
    async def join(self, i: discord.Interaction, button: discord.ui.Button):
        current_players = readfromFile(player_path)
        if i.user.id in current_players: 
            return await i.response.send_message("Eager today, aren't we?", ephemeral=True)
        return await i.response.edit_message(embed = corpseViewEmbed(self.bot, i.user.id, "join"))
    @discord.ui.button(label = "Leave")
    async def leave(self, i: discord.Interaction, button: discord.ui.Button):
        current_players = readfromFile(player_path)
        if i.user.id not in current_players: 
            return await i.response.send_message("If a tree falls in the forest...", ephemeral=True)
        return await i.response.edit_message(embed = corpseViewEmbed(self.bot, i.user.id, "leave"))
    
    @discord.ui.button(label = "Shuffle")
    async def shuffle(self, i: discord.Interaction, button: discord.ui.Button):
        return await i.response.edit_message(embed = shuffleViewEmbed(self.bot)) 

    @discord.ui.button(label = "Start")
    async def start(self, i: discord.Interaction, button: discord.ui.Button):
        if i.user.id != chief_executor or not readfromFile(player_path): 
            return await i.response.send_message("Oi, don't touch the corpse until it's ready", ephemeral=True)
        await self.message.edit(view = None)

        # start the corpse!
        embed, nextup = beginCorpseEmbed(self.bot) # find who's next 
        await i.response.edit_message(embed = embed) 
        await self.bot.get_user(int(nextup)).send("yer up")

    async def on_timeout(self) -> None:
        await self.message.edit(view = None)

class corpse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("corpse is Ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        # If guards because on_message fires CONSTANTLY
        if message.guild is not None: return
        if message.author.bot: return
        if message.content and message.content[0] == "~": return

        # check if there's a corpse going on
        checkList = readfromFile(player_path)
        if not checkList: return

        # check if user is going in turn
        if len(checkList) <= checkList["HotSeat"]: return
        hotSeat = list(checkList.keys())[checkList["HotSeat"]]
        if (message.author.id != int(hotSeat)):
            return await message.channel.send("I'm sorry but it's not your turn to go, `~check` for the correct order")
        
        # Check if the message has attachments 
        if (message.attachments):
            # responses for submitting corpse
            responses = ["OMG IT'S BEAUTIFUL 😍", "OMG IT'S HIDEOUS, just how I like them 😌", \
                    "So very based of you", "peko", "Thank you for your corpse, have a nice day <:salute:659228687958409218>",
                    "*chefs kiss*"]
            
            corpse_list = readfromFile(corpse_path)
            corpse_list.append(message.attachments[0].url)
            writetoFile(corpse_list, corpse_path)

            # great job bro
            await message.channel.send(choice(responses))
            emoji = self.bot.get_emoji(926281518266073088)
            await message.add_reaction(emoji)

            # mark as done - if corpse done return
            oldSeat, newHotSeat = passingTheCorpse("<:check:926281518266073088>")
            if newHotSeat == "True":
                await message.channel.send("You've reached the end of the line! I'm sure your ending was a stinger :D")
                celebrate = ["<:Smug:1132402749619843125>", ":tada:", "<:kirby:561033037521879069>", "<:goppers:940834491730124831>"]
                return await self.bot.get_channel(809686249999826955).send(f"Corpse is done baking! It's ready to be taken out of the oven now {choice(celebrate)}! `c!deliver` to view your completed corpse!")
            await self.bot.get_user(int(newHotSeat)).send(f"yer up! [⠀]({message.attachments[0].url})")

        else:
            emoji = self.bot.get_emoji(926283850882088990)
            await message.add_reaction(emoji)
            await message.channel.send("Please attach a corpse to your message as a file, ty")
    
    # Commands
    @commands.command(aliases=["sc", "cs"])
    async def startCorpse(self, ctx):
        # corpse already started
        # if (readfromFile(player_path)):
        #     return await ctx.send(f"Please `{ctx.prefix}clean` up after you're finished with your corpse")
        
        view = CorpseView(self.bot)
        view.message = await ctx.send(embed = corpseViewEmbed(self.bot), view = view)

    @commands.command()
    async def check(self, ctx):
        if (randint(0, 50) < 1):
            return await ctx.send("What am I, an ATM machine?")
        
        checkList = readfromFile(player_path)
        if (checkList):
            checkList.pop("HotSeat") # don't print hotseat
            prettyList = [f"{value} {self.bot.get_user(int(key)).name}" for key, value in checkList.items()]
            await ctx.send("\n".join(prettyList))
        else:
            await ctx.send(f"Your corpse game is lacking, step it up with `{ctx.prefix}cs`")

    @commands.command()
    @commands.is_owner()
    async def skip(self, ctx):
        checkList = readfromFile(player_path)
        if (checkList):
            oldHotSeat, newHotSeat = passingTheCorpse("<:cross:926283850882088990>")
            await ctx.invoke(self.bot.get_command("check"))
            if newHotSeat == "True":
                return await ctx.send(f"You've reached the end of the line! `{ctx.prefix}deliver` to view the completed corpse!")
            corpse_list = readfromFile(corpse_path)
            try:
                await self.bot.get_user(int(newHotSeat)).send(f"yer up! [⠀]({corpse_list[oldHotSeat]})")
            except Exception as e:
                print(oldHotSeat)
                print(corpse_list)
                print(e)

    @commands.command()
    async def clean(self, ctx):
        if ctx.author.id != chief_executor:
            return await ctx.send(choice(missing_perms))
        oldCorpse = readfromFile(corpse_path)
        if oldCorpse == []:
            return await ctx.send("Your corpse has already been successfully disposed of")
        
        # clear players
        writetoFile([], player_path)
        # clear corpse
        writetoFile([], corpse_path)
        timestamp = datetime.today().strftime("%Y-%m-%d")
        writetoFile(oldCorpse, f"corpse/CorpseArchive2023/oldCorpse-{timestamp}")

        responses = ["https://tenor.com/view/chores-cleaning-housework-tom-and-jerry-housewife-gif-20706096",
                     "Fear not, the bodies are buried where no one will find them now (:",
                     "*sounds of vaccuum and whirring brooms*"]
        await ctx.send(choice(responses))

    @commands.command()
    async def deliver(self, ctx):
        checkList = readfromFile(player_path)
        hotSeat = checkList["HotSeat"]
        checkList.pop("HotSeat") # don't print hotseat
        
        if hotSeat != len(checkList):
            return await ctx.send("Your corpse has not finished baking!")
        
        corpse_links = readfromFile(corpse_path)
        await ctx.send("One freshly baked corpse coming right up!")


        corpseEmbedList = []
        for i, ((key, value), link )in enumerate(zip(list(checkList.items()), corpse_links)):
            artist = self.bot.get_user(int(key))
            corpseEmbed = discord.Embed(
                title=f"{i+1}. {artist.name}",
                timestamp=discord.utils.snowflake_time(int(re.search(r'\d{17,20}/(\d{17,20})', link).group(1)))
            )
            corpseEmbed.set_footer(text="Submited", icon_url=artist.avatar.url)
            corpseEmbed.set_image(url=link)
                
            corpseEmbedList.append(corpseEmbed)

        for i in range(0, len(corpse_links), 5):
            await ctx.send(embeds=corpseEmbedList[i:i+5])
        # # Combine every 5 strings
        # combined_strings = [''.join([f"{self.bot.get_user(int(key)).name} [⠀]({link})\n" for (key, value), link in zip(list(checkList.items())[i:i+5], corpse_links[i:i+5])]) for i in range(0, len(corpse_links), 5)]

        # # Send each combined string
        # for combined_string in combined_strings:
        #     await ctx.send(combined_string) 

    @commands.command(aliases=["ch"])
    async def corpseHelp(self, ctx):
        p = ctx.prefix
        embed = discord.Embed(
            title = "Corpse Bot v2",
            description = f"""
            `{p}cs` ➙ Starts a new corpse 
            `{p}check` ➙ Checks the status of current corpse
            `{p}skip` ➙ Skips someone (use with caution)
            
            `{p}clean` ➙ Cleans & archives old corpse
            `{p}deliver` ➙ Send a finished corpse

            `{p}corpseHelp` ➙ Brings up this menu 
            """,
            color=randomHexGen(),
            url=choice(oldCorpses))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(corpse(bot))