import discord
import random
from discord.ext import commands

class extraCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("botFun is Ready")

    # Commands
    @commands.command()
    async def add(self, ctx, left: int, right: int):
    #Adds two numbers together
        await ctx.send(left + right)

    @commands.command()
    async def avatar(self, ctx, *, member : discord.Member=None):
        if not member:
            member = ctx.message.author
        pfp = member.avatar_url
        embed = discord.Embed()
        embed.set_image(url=pfp)
        await ctx.send(embed=embed)

    @commands.command()
    async def joined(self, ctx, *, member: discord.Member=None):
        if not member:
            member = ctx.message.author
        await ctx.send('{0} joined on {0.joined_at}'.format(member))

#➥ 8Ball Command
    @commands.command(aliases=["8ball", "8b"])
    async def _8ball(self, ctx, *, question):
        member = ctx.message.author
        responses = ["It is certain.",
                    "It is decidedly so.",
                    "Without a doubt.",
                    "Yes - definitely.",
                    "You may rely on it.",
                    "As I see it, yes.",
                    "Most likely.",
                    "Outlook good.",
                    "Yes.",
                    "Signs point to yes.",
                    "Reply hazy, try again.",
                    "Ask again later.",
                    "Better not tell you now.",
                    "Cannot predict now.",
                    "Concentrate and ask again.",
                    "Don't count on it.",
                    "My reply is no.",
                    "My sources say no.",
                    "Outlook not so good.",
                    "Very doubtful." ]
        await ctx.send(f"{member.display_name}: {question}\n<:8ball:845546744665735178> says {random.choice(responses)}")
##

def setup(bot):
    bot.add_cog(extraCommands(bot))



