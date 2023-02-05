import random
import re
from datetime import datetime, timedelta, date
from math import ceil
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import GuildConverter, MemberConverter
from myutils.poll_class import readfromFile, writetoFile
from main import randomHexGen

class extraCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("botFun is Ready")

    # Commands
    @commands.command()
    async def math(self, ctx, flag:str, *nums):
        if flag == "add" or flag == "+":
            eq = " + ".join(nums)
            try:
                result = sum([int(i) for i in nums])
            except Exception:
                await ctx.send(f"Only integers, format is {ctx.prefix}math add 2 3 4")
        elif flag == "multiply" or flag == "*":
            eq = " * ".join(nums)
            try:
                result = [b := 1, [b := b * a for a in [int(i) for i in nums]]][-1][-1]
            except Exception:
                return await ctx.send(f"Only integers, format is {ctx.prefix}math multiply 2 3 4")
        else:
            return await ctx.send("Cannot do division, sorry!")

        embed = discord.Embed (
            title = "Result",
            description = f"{eq} = {result}",
            color = randomHexGen()
        )
        await ctx.send(embed = embed)

    @commands.command()
    async def avatar(self, ctx, *, given_id = None):
        embed = discord.Embed()
        if given_id:
            try:
                guild = await GuildConverter().convert(ctx, given_id)
                embed.set_image(url=guild.icon)
            except commands.BadArgument:
                member = await MemberConverter().convert(ctx, given_id)
                embed.set_image(url=member.avatar.url)
        else:
            given_id = ctx.message.author
            embed.set_image(url=given_id.avatar.url)
        await ctx.send(embed = embed)

    @avatar.error
    async def avatar_error(self, ctx, error):
        await ctx.send(f"Server/{error} \nOnly works with members I've seen or servers I'm in...")

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
                "Always forgive your enemies; nothing annoys them so much.", "https://www.lewdlegame.com/", "https://t.co/fmog2jz7U8",
                "https://www.hogwartsishere.com/hogwartle",
                "https://nerdlegame.com/", "https://zaratustra.itch.io/dordle", "https://qntm.org/files/wordle/index.html",
                "https://pbs.twimg.com/media/FTxa2AYXwAEHagd.jpg"]
        await ctx.send(random.choice(eggs))
##

#* Tatsu
    @commands.command(aliases = ["tgCheck"])
    @commands.is_owner()
    async def tgcheck(self, ctx, *, inp=None):
        # xp50Total = 255000
        if inp:
            total = int(inp.split(" ")[1])
            xpNow = int(inp.split(" ")[0])
            xpNeeded = total - xpNow

            trainNeededMax = xpNeeded / 10
            trainNeededMin = xpNeeded / 14

            minTimeSecs = trainNeededMin * 45
            maxTimeSecs = trainNeededMax * 45

            minTimeMinutes = round(minTimeSecs/60, 3)
            maxTimeMinutes = round(maxTimeSecs/60, 3)

            minTimeHours = round(minTimeMinutes/60, 3)
            maxTimeHours = round(maxTimeMinutes/60, 3)

            embed = discord.Embed(
                title = "Tatsugotchi Experience Progress",
                description = f"""
                Needed XP to reach next level: **{xpNeeded}**
                # of `t!tg train` needed: from {round(trainNeededMin)} to {round(trainNeededMax)}
                Time Needed (if `train` every 45 seconds):
                **{minTimeMinutes}** - **{maxTimeMinutes}** minutes
                ...roughly **{minTimeHours}** - **{maxTimeHours}** hours.
                """,
                color = randomHexGen()
            )
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"`{ctx.prefix}tgCheck <current xp> <xp needed for next level>`")

    #* checkVotes
    @commands.command(aliases = ["checkVote", "checkvote", "votecheck", "checkVotes", "checkvotes"])
    @commands.is_owner()
    async def voteCheck(self, ctx, *, inp = None):
        if inp:
            #today = datetime(2022, 11, 26, 11, 59) # currently includes the 26th interestingly, need to calculate differently modulo?
            today = datetime.now()
            nextMonth = today.month + 1 # Calculate next month
            if nextMonth == 13: # if December wrap around
                nextMonth = 1
            # don't need to subtract one, I was not fully counting last day
            lastDay = date(today.year, nextMonth, 1) - timedelta(days = 1)
            
            daysLeft = lastDay.day - today.day
            print(daysLeft)
            timeLeft = today - datetime(today.year, nextMonth, 1)

            inp = inp.split(" ")
            try:
                currVotes, totalVotes, coolDown = inp
            except ValueError:
                currVotes, totalVotes = inp
                coolDown = 0

            votesNeeded = int(totalVotes) - int(currVotes)
            timeLeft = timeLeft + timedelta(hours = int(coolDown)) # datetime object
            hoursLeft = timeLeft.total_seconds()/3600 * -1 # hours float
            chances = hoursLeft/24 * 4 # integer

            await ctx.send(f"""
votes needed: `{votesNeeded}`
hours left (minus cooldown): `{round(hoursLeft, 3)}`
chances left to vote (rounded up to next even): `{ceil(chances/2.) * 2}`
expected votes per day: `{votesNeeded/daysLeft}`
            """)
        else:
            await ctx.send(f"`{ctx.prefix}checkVotes <# of votes so far> <total votes needed> [cooldown(hrs)]`")
##

#* Emoji
    @commands.command(aliases = ["emoji"])
    async def emojify(self, ctx, *, inp: str):
        emoji = inp.lower()
        if emoji.lower() in ['list', 'help']:
            embed = discord.Embed(
                title="List of stored emojis",
                description="",
                color = randomHexGen()
            )
            embed.add_field(name="HGSS",
            value=""" Smug, Hide, Adore,
            <:smug:940834492334108692> <:hide:940834492350877697> <:adore:940834492292137001>
            Harrysweat, Archiehehe, Laughcry, Dracostabbed
            <:harrysweat:940834492212453376> <:archiehehe:940834491574927361> <:laughcry:940834492514467860> <:dracostabbed:982859131687956501>
            """)
            embed.add_field(name="David's Server",
            value=""" Damn, Lolric, Degrence,
            <:damn:940834491268735046> <:loric:940834491675574272> <:degrence:940834491683971092>
            Humber, Goppers, Teluge,
            <:humber:940834492376039494> <:goppers:940834491730124831> <:teluge:940834491784646738>
            Splat, Baho, Nharwhal
            <:splat:940834491063226419> <:baho:940834491646242866> <:nharwhal:940839334989422632>""")
            #embed.add_field(name="\u200b", value="\u200b",inline=False)
            embed.add_field(name="Danny & Testing Server",
            value=""" Fear, Pain, Agony
            <:pain:940834492275359794> <:fear:940834492107620394> <:agony:940834452173623317>
            Wave, Birdy, Murder
            <:twiggwave:940834492308934706> <a:Birdy:845590890240278579> <:murder:941189017549021235>
            """)
            embed.add_field(name="Roos & Turtles",
            value=""" RooLove, RooClap, RooCool
            <a:rooLove:982859137895522374> <a:rooClap:982859135118901318> <:rooCool:982859136230387752>
            TurtleClap, Turtleparty, Turtlepurple
            <a:turtleclap:982859141762646086> <a:turtleparty:982859142928691240> <:turtlepurple:982859144086315078>
            """)
            embed.add_field(name="Animated & Happy",
            value=""" Thisisfine, Pikawoo, Atada
            <a:thisisfine:982859140265279498> <a:pikawoo:982859133973835856> <a:atada:982859129464967218>
            Cathappy, Ghosthug, Stab, Ty
            <:catHappy:982859130584858624> <:ghosthug:982859132849762374> <:stab:982859139048960020> <:ty:982859145185214484>
            """)

            await ctx.send(embed=embed)
            return

        try:
            key = re.search(r"(?<=`).*(?=`)", emoji).group() #Finds first object
        except AttributeError:
            key = None

        emojiDict = {
            "adore": "https://cdn.discordapp.com/attachments/752637404828926012/940835507506655242/adore.png",
            "agony": "https://cdn.discordapp.com/attachments/752637404828926012/940835507808653392/agony.png",
            "archiehehe": "https://cdn.discordapp.com/attachments/752637404828926012/940835508202922004/archiehehe.png",
            "baho": "https://cdn.discordapp.com/attachments/752637404828926012/940835851955478548/baho.png",
            "damn": "https://cdn.discordapp.com/attachments/752637404828926012/940835506009296897/damn.png",
            "degrence": "https://cdn.discordapp.com/attachments/752637404828926012/940835506277711873/degrence.png",
            "fear": "https://cdn.discordapp.com/attachments/752637404828926012/940835506533576745/fear.png",
            "goppers": "https://cdn.discordapp.com/attachments/752637404828926012/940835506797821992/goppers.png",
            "harrysweat": "https://cdn.discordapp.com/attachments/752637404828926012/940835507175301190/harrysweat.png",
            "hide": "https://cdn.discordapp.com/attachments/752637404828926012/940835524917223434/hide.png",
            "humber": "https://cdn.discordapp.com/attachments/752637404828926012/940835525181452359/humber.png",
            "laughcry": "https://cdn.discordapp.com/attachments/752637404828926012/940835523214323732/laughcry.png",
            "loric": "https://cdn.discordapp.com/attachments/752637404828926012/940835523465998346/loric.png",
            "pain": "https://cdn.discordapp.com/attachments/752637404828926012/940835523705053254/pain.png",
            "smug": "https://cdn.discordapp.com/attachments/752637404828926012/940835524032200754/smug.png",
            "splat": "https://cdn.discordapp.com/attachments/752637404828926012/940835524220977202/splat.png",
            "teluge": "https://cdn.discordapp.com/attachments/752637404828926012/940835525181452359/humber.png",
            "wave": "https://cdn.discordapp.com/attachments/752637404828926012/940835524665548810/wave.png",
            "birdy": "https://cdn.discordapp.com/attachments/806952740424384573/941188500877893672/birdy.gif",
            "murder": "https://cdn.discordapp.com/attachments/806952740424384573/941187707068121129/murder_v_2_Custom.png",
            "rooclap": "https://cdn.discordapp.com/attachments/806952740424384573/982855921980022815/rooClap.gif",
            "roolove": "https://cdn.discordapp.com/attachments/806952740424384573/982855922504319016/rooLove.gif",
            "roocool": "https://cdn.discordapp.com/attachments/806952740424384573/982855922252644382/rooCool.png",
            "turtlepurple": "https://cdn.discordapp.com/attachments/806952740424384573/982856298112639036/turtlepurple.png",
            "turtleparty": "https://cdn.discordapp.com/attachments/806952740424384573/982856298376867840/turtleparty.gif",
            "turtleclap": "https://cdn.discordapp.com/attachments/806952740424384573/982856298745974805/turtleclap.gif",
            "pikawoo": "https://cdn.discordapp.com/attachments/806952740424384573/982856634390949958/pikawoo.gif",
            "dracostabbed": "https://cdn.discordapp.com/attachments/806952740424384573/982856634650984498/dracostabbed.png",
            "nharwhal": "https://cdn.discordapp.com/attachments/806952740424384573/982856936091439174/nharwhal.png",
            "ty": "https://cdn.discordapp.com/attachments/806952740424384573/982856936322105395/ty.png",
            "ghosthug": "https://cdn.discordapp.com/attachments/806952740424384573/982856936577986660/ghosthug.png",
            "cathappy": "https://cdn.discordapp.com/attachments/806952740424384573/982857375734202368/catHappy.png",
            "stab": "https://cdn.discordapp.com/attachments/806952740424384573/982857526880133180/stab.png",
            "thisisfine": "https://cdn.discordapp.com/attachments/806952740424384573/982857527140155402/thisisfine.gif",
            "atada": "https://cdn.discordapp.com/attachments/806952740424384573/982857527383457852/atada.gif"
        }
        if key is not None:
            if emojiDict.get(key):
                msgEmojid = "Copy and paste this image to send to friends! " + emojiDict.get(key)
                try:
                    await ctx.guild.get_member(ctx.author.id).send(msgEmojid)
                except AttributeError:
                    await ctx.send(msgEmojid)
            else:
                await ctx.send("Emoji not found in dictionary")
        else:
            await ctx.send(f"Syntax: {ctx.prefix}emojify \`{emoji}\`")

##

#* Profile Pictures
    @commands.command(aliases = ["pfps", "profiles"])
    async def pfp(self, ctx, inp: str, newKey = None, newLink = None):
        flag = inp.lower()

        pfps_dict = readfromFile("pfps")
        if flag == "show":
            if newKey:
                return await ctx.send(f"**{newKey}**\n{pfps_dict[newKey]}")
            for key, link in pfps_dict.items():
                await ctx.send(f"**{key}**\n{link}")

        elif flag == "list":
            for key, link in pfps_dict.items():
                await ctx.send(f"**{key}**")

        elif flag == "save":
            pfps_dict[newKey] = newLink
            writetoFile(pfps_dict, "pfps")
            return await ctx.send("pfp saved!")

        elif flag == "delete" or flag == "remove":
            del pfps_dict[newKey]
            writetoFile(pfps_dict, "pfps")
            return await ctx.send("pfp deleted!")

        else:
            await ctx.send("Options are `list/show`, `show <key>`, `delete/remove <key>`, `save <key> <link>`, `help`")
##

#* Shuffle a list
    @commands.command()
    async def shuffle(self, ctx, *, inp: str):
        inp_list = inp.split("\n")
        random.shuffle(inp_list)
        await ctx.send("\n".join(inp_list))

##

    #* Help with Admin Commands
    @commands.command(aliases = ["@help"])
    @commands.is_owner()
    async def adminHelp(self, ctx):
        await ctx.send(f"""
```
Don't need to put `@` in front
{" POLL ":.^10}
{ctx.prefix}vote insertPoll <string input formatted json>
{ctx.prefix}vote clear (clears dictionary)
{ctx.prefix}vote saveReset
```
```
Don't need to put `@` in front
{" FUN ":.^11}
{ctx.prefix}timeConvert (runs humantimeTranslator)
{ctx.prefix}tgCheck <current xp> <xp needed for next level>
{ctx.prefix}voteCheck <# of votes so far> <total votes needed>
{ctx.prefix}pfps help
```
```
{"CLIBOPBOPRD":📋^13}
{ctx.prefix}list @view
```
""")

async def setup(bot):
    await bot.add_cog(extraCommands(bot))
