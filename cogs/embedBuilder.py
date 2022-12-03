import discord
import random
from discord.ext import commands
from datetime import datetime

ratingColors = {
    "teens": 0xE5D100,
    "explicit": 0x9B0000,
    "general": 0x78A704,
    "mature": 0xE1730D,
    "unspecified":0x0
}

class embedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("embedBuilder is Ready")

    # Commands
    @commands.command()
    async def sendEmbed(self, ctx):
        embed = discord.Embed(
            title = "Mind Magic",
            description = "by [Snickerdoodlepop](https://archiveofourown.org/users/Snickerdoodlepop/pseuds/Snickerdoodlepop)",
            color = ratingColors["teens"]
        )
        embed.add_field(name="Fandoms:", value="Harry Potter - J. K. Rowling", inline=False)
        embed.add_field(name="Summary:", value="""
        Once Voldemort realizes that Harry Potter is his horcrux, his plans change drastically. So does Draco Malfoy's assignment for the school year.
        Harry's sixth year starts going very differently. Snape is on a mission. Harry needs to learn pureblood politics…        
        """, inline=False)

        embed.add_field(name="Rating:", value="<:Teens:1048513348599304252> Teen And Up Audiences")
        embed.add_field(name="Warnings:", value="Graphic Depictions Of Violence, Underage")
        embed.add_field(name="**Words: 302405**", value="""
        **Kudos: 6560**
        **Bookmarks: 1900**
        """)

        embed.add_field(name="Relationships:", value="Harry Potter/Voldemort, Harry Potter/Tom Riddle, Remus Lupin/Nymphadora Tonks, …", inline=False)
        embed.add_field(name="Characters:", value="Ron Weasley, Hermione Granger, Severus Snape, …", inline=False)
        embed.add_field(name="Tags:", value="Political!Harry, light!harry, Dark!Voldemort, Well-Meaning Dumbledore, Possessive Voldemort, … ", inline=False)

        # embed.add_field(name="\u2800", value=field2, inline=False)
        embed.add_field(name="Series:", value="**Part 1** of [Harry Potter and the Search for Ancient Magic](https://archiveofourown.org/series/1133141)", inline=False)
        embed.add_field(name="Chapters:", value="28/28 Completed ✓")
        embed.add_field(name="Updated:", value=datetime.strftime(datetime.strptime("2021-02-06", "%Y-%m-%d"), "%B %d, %Y"))
        embed.add_field(name="Categories:", value="Multi")

        embed.url = "https://archiveofourown.org/works/15994781/chapters/37317395"
        embed.set_thumbnail(url="https://archiveofourown.org/images/ao3_logos/logo_42.png")
        embed.set_footer(text=f"Linked by {ctx.message.author}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(embedBuilder(bot))