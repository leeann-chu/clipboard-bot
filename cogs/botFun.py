import discord
import random
import math
from discord.ext import commands
from main import randomHexGen
import asyncio

class extraCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("botFun is Ready")

    # Commands
    @commands.command()
    async def add(self, ctx, *nums):
        eq = " + ".join(nums)
        try:
            summation = sum([int(i) for i in nums])
        except Exception:
            await ctx.send(f"Only integers, format is {ctx.prefix}add 2 3 4")
        embed = discord.Embed (
            title = "Summation",
            description = f"{eq} = {summation}",
            color = randomHexGen()
        )
        await ctx.send(embed = embed)

    @commands.command()
    async def avatar(self, ctx, *, member : discord.Member=None):
        if not member:
            member = ctx.message.author
        embed = discord.Embed()
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def chooseOne(self, ctx, *, inp : str):
        inputList = inp.split(" ")
        await ctx.send(random.choice(inputList))

    @commands.command()
    async def joined(self, ctx, *, member: discord.Member=None):
        if not member:
            member = ctx.message.author
        joinedTime = member.joined_at
        await ctx.send(f"{member} ({member.display_name}) joined on <t:{int(joinedTime.timestamp())}:f>")

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

#➥ Hello Command
    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Say hello!")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try: 
            msg = await self.bot.wait_for('message', check = check, timeout = 15)
            if (msg.content) == 'hello':
                await ctx.send(f"Hello {msg.author.display_name}!")   
            else:
                await ctx.send("rude!")  
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.display_name} did not respond in time!", delete_after = 5)   
##

#➥ Repeat Command
    @commands.command(aliases=['mimic', 'copy'])
    async def repeat(self, ctx, *, inp: str):
        await ctx.send(inp)

    @repeat.error
    async def repeat_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'inp':
                await ctx.send("You forgot to give me input to repeat!")
##

#➥ Easteregg
    @commands.command(aliases=['egg', 'secret'])
    async def easteregg(self, ctx):
        eggs = ["https://imgur.com/gallery/Sn3R1", "https://cdn.discordapp.com/attachments/806952740424384573/881582644020772894/unknown.png", 
                "https://www.youtube.com/watch?v=Xx8TQfhRVXY", "http://howardhallis.com/POE/index.html", 
                "https://media.discordapp.net/attachments/806952740424384573/881583866249351278/name_of_the_wind_fanart_cover.jpg?width=439&height=670", 
                "I'm sorry I slapped you but you didn't seem like you would ever stop talking and I panicked",
                "https://cdn.discordapp.com/attachments/806952740424384573/881585486496403487/Screenshot_20170901-221337.png",
                "https://cdn.discordapp.com/attachments/806952740424384573/881585743510773800/sarah_cat_august.gif",
                "https://cdn.discordapp.com/attachments/806952740424384573/881585832010604605/cat_cup_crop_-_june.gif",
                "What is the height of stupidty? \nI don't know, how tall are you?",
                "The most beautiful things in the world cannot be seen or touched, they are felt with the heart.",
                "Happy people are just people you aren't acquainted enough with yet to know how miserable they really are",
                "Always forgive your enemies; nothing annoys them so much."]
        await ctx.send(random.choice(eggs))
##

def setup(bot):
    bot.add_cog(extraCommands(bot))



