import discord
from discord.ext import commands
from main import randomHexGen
from utils.poll_class import readfromFile, writetoFile
import re

# Functions
def scoreboardEmbed(type_of_board):
    board_type = {}
    if type_of_board == "emoji":
        board_type = readfromFile("emoji_count")
    elif type_of_board == "member":
        board_type = readfromFile("member_emoji")
    else:
        board_type = readfromFile("emoji_count")

    scoreboard = []
    embed = discord.Embed(
        title = "Most emotive members" if type_of_board == "member" else "Most used emojis",
        description = "placeholder",
        color = randomHexGen(),
        timestamp = discord.utils.utcnow()
    )
    if board_type:
        for item in sorted(((v, k) for k, v in board_type.items()), reverse=True):
            if item[0] > 10:
                scoreboard.append(f"{item[0]} {item[1]}")

    #* Forming the embed
    embed.description = "\n".join(scoreboard) if scoreboard else "No data found!"
    return embed

#* Emoji SB View
class scoreboard(discord.ui.View):
    def __init__(self):
        super().__init__()
    #Add our three buttons
    @discord.ui.button(label = "Emoji")
    async def back(self, i:  discord.Interaction, button: discord.ui.Button):
        await i.response.edit_message(embed = scoreboardEmbed("emoji"))

    @discord.ui.button(label = "Member")
    async def member(self, i:  discord.Interaction, button: discord.ui.Button):
        await i.response.edit_message(embed = scoreboardEmbed("member"))

    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.primary)
    async def refresh(self, i:  discord.Interaction, button: discord.ui.Button):
        if i.message.embeds[0].title == "Most emotive members":
            await i.response.edit_message(embed = scoreboardEmbed("member"))
        else:
            await i.response.edit_message(embed = scoreboardEmbed("emoji"))

    async def on_timeout(self) -> None:
        await self.message.edit(view = None)

class emoji_sb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("emoji_sb is Ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if isinstance(message.channel, discord.channel.DMChannel): return
        if message.guild.id != 370200859675721728: return
        #if message.guild.id != 416749994163568641: return
        emoji_found = re.findall(r"[^\x00-\x7F™️ę’”“€]+|(?::|<:|<a:)(?:\w{1,64}:\d{17,18}|(?:\w{1,64}))(?::|>)", message.content, re.IGNORECASE)

        if not emoji_found: return #checks if there are emoji in message

        emoji_count = readfromFile("emoji_count")
        member_emoji_count = readfromFile("member_emoji")

        #print(f"Emoji found list {list(emoji_found)}")
        for emoji in emoji_found:
            default_emoji = emoji_count.setdefault(emoji, 0)
            if default_emoji >= 0: emoji_count[emoji] += 1

            default_member = member_emoji_count.setdefault(message.author.name, 0)
            if default_member >= 0: member_emoji_count[message.author.name] += 1

        #print(member_emoji_count)
        #print(f"{emoji_count} \n")
        writetoFile(member_emoji_count, "member_emoji")
        writetoFile(emoji_count, "emoji_count")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot: return
        if payload.guild_id != 370200859675721728: return
        #if payload.guild_id != 416749994163568641: return
        emoji_count = readfromFile("emoji_count")
        member_emoji_count = readfromFile("member_emoji")

        default_emoji = emoji_count.setdefault(str(payload.emoji), 0)
        if default_emoji >= 0: emoji_count[str(payload.emoji)] += 1

        default_member = member_emoji_count.setdefault(payload.member.name, 0)
        if default_member >= 0: member_emoji_count[payload.member.name] += 1

        #print(member_emoji_count)
        #print(emoji_count)
        writetoFile(member_emoji_count, "member_emoji")
        writetoFile(emoji_count, "emoji_count")

    # Commands
    @commands.command(aliases=["lb", "sb", "leaderboard", "score board", "leader board"])
    async def scoreboard(self, ctx, *, type_of_board = None):
        if type_of_board == "member" or type_of_board == "emoji" or type_of_board == None:
            view = scoreboard()
            view.message = await ctx.send(embed = scoreboardEmbed(type_of_board), view = view)
        else:
            await ctx.send("Uknown board type, options are `member` or `emoji`")

async def setup(bot):
    await bot.add_cog(emoji_sb(bot))
