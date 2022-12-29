import discord
import random
from discord.ext import commands
from datetime import datetime
from bs4 import BeautifulSoup
import cloudscraper 
import requests

# The regular expressions to identify AO3 and FFN links.
# Note there may be an extra character at the beginning, due to checking
# the previous character to verify it is not ! (which would not match)
# AO3_MATCH = re.compile (
#     "(^|[^!])https?:\\/\\/(www\\.)?archiveofourown.org(\\/collections\\/\\w+)?\\/(works|series)\\/\\d+")

HEADERS = {"User-Agent": "fanfiction-abstractor-bot"}
FFN_GENRES = set()
# create scraper to bypass cloudflare, always download desktop pages
options = {"desktop": True, "browser": "firefox", "platform": "linux"}
scraper = cloudscraper.create_scraper(browser=options)

ratingColors = {
    "Teen And Up Audiences": 0xE5D100,
    "Explicit": 0x9B0000,
    "General Audiences": 0x78A704,
    "Mature": 0xE1730D,
    "Not Rated":0xFFFFFF
}

ratingEmoji = {
    "Teen And Up Audiences": "<:teens:1057882444654706728>",
    "Explicit": "<:explicit:1057882406176165950>",
    "General Audiences": "<:general:1057882417580494878>",
    "Mature": "<:mature:1057882440334585907>",
    "Not Rated":":white_medium_square:",

    "Gen": "<:gen_cat:1057884762842353734>",
    "F/M": "<:het:1057882423234404463>",
    "M/M": "<:mm:1057882427558744124>",
    "F/F": "<:ff:1057882410097852466>",
    "Other": "<:other:1057882436568100935>",

    "Multi": "<:multi:1057882432239583282>"
}

def format_html(field):
    """Format an HTML segment for discord markdown.
    field should be a note or summary from AO3.
    """
    brs = field.find_all("br")
    for br in brs:
        br.replace_with("\n")
    ols = field.find_all("ol")
    for ol in ols:
        ol.name = "p"
    uls = field.find_all("ul")
    for ul in uls:
        ul.name = "p"
    for li in field.find_all("li"):
        li.string = "- {}".format(li.text.strip())
        li.unwrap()
    field = field.blockquote.find_all("p")
    result = list(map(lambda x: x.text.strip(), field))
    result = "\n\n".join(result)
    if len(result) > 250:
        result = result[:250] + "…"
    return result
    
def generate_ao3_work_summary(link):
    """Generate the summary of an AO3 work.
    link should be a link to an AO3 fic
    Returns the message with the fic info, or else a blank string
    """
    r = requests.get(link, headers=HEADERS)
    if r.status_code != requests.codes.ok:
        return ""
    if r.url == "https://archiveofourown.org/users/login?restricted=true":
        return ""
    soup = BeautifulSoup(r.text, "lxml")
    ficPieces = {}

    preface = soup.find(class_="preface group")
    ficPieces["title"] = preface.h2.string.strip()
    ficPieces["link"] = link
    author = preface.h3.string
    multi_author = []
    if author is None:
        multi_author = [f"""[{name.string}](https://archiveofourown.org{name["href"]})""" for name in preface.h3.find_all("a")]
        ficPieces["author"] = "by " + ", ".join(multi_author)
    else:
        ficPieces["author"] = "" +  author.strip()

    summary = preface.find(class_="summary module")
    if summary:
        ficPieces["summary"] = format_html(summary)

    tags = soup.find(class_="work meta group")
    rating = tags.find("dd", class_="rating tags")
    category = tags.find("dd", class_="category tags")
    fandoms = tags.find("dd", class_="fandom tags")
    warnings = tags.find("dd", class_="warning tags")
    relationships = tags.find("dd", class_="relationship tags")
    characters = tags.find("dd", class_="character tags")
    freeform = tags.find("dd", class_="freeform tags")
    series = tags.find("dd", class_="series")
    bookmarks = tags.find("dd", class_="bookmarks")
    words = tags.find("dd", class_="words")
    chapters = tags.find("dd", class_="chapters")
    kudos = tags.find("dd", class_="kudos")

    ficPieces["kudos"] = kudos.string if kudos else 0
    ficPieces["bookmarks"] = bookmarks.string if bookmarks else 0
    ficPieces["words"] = words.string if words else 0
    
    completed = tags.find("dt", class_="status") # can be none
    updated = tags.find("dd", class_="status") 
    checkmark = ""
    if updated or completed: # updated & published / completed & published
        ficPieces["status"] = completed.string
        ficPieces["updated"] = updated.string
        checkmark = " Completed :white_check_mark:"
    else: # neither updated or completed
        ficPieces["status"] = "Published:"
        ficPieces["updated"] = tags.find("dd", class_="published").string

    if chapters:
        part, whole = chapters.string.split("/")
    if part == whole:
        ficPieces["chapters"] = chapters.string + checkmark 
    else:
        ficPieces["chapters"] = chapters.string

    multi_series = ""
    if series:
        for s in series.find_all(class_="position")[:5]:
            s_name = s.text.split()
            s = f"""**Part {s_name[1]}** of **[{" ".join(s_name[3:])}](https://archiveofourown.org{s.a["href"]})**\n"""
            multi_series += s
        ficPieces["series"] = multi_series

    if fandoms:
        fandoms = list(map(lambda x: x.string, fandoms.find_all("a")))
        if len(fandoms) > 5:
            ficPieces["fandoms"] = ", ".join(fandoms[:5]) + "…"
        else:
            ficPieces["fandoms"] = ", ".join(fandoms)

    if rating:
        ficPieces["rating"] = ", ".join(map(lambda x: x.string, rating.find_all("a")))
    if category: 
        ficPieces["category"] = ", ".join(map(lambda x: x.string, category.find_all("a")))  
        
    ficPieces["warnings"] = ", ".join(map(lambda x: x.string, warnings.find_all("a")))
    if relationships:
        ficPieces["character_heading"] = "Additional Characters:"
        relationships = list(map(lambda x: x.string, relationships.find_all("a")))
        if len(relationships) > 4:
            ficPieces["relationships"] = ", ".join(relationships[:4]) + "…"
        else:
            ficPieces["relationships"] = ", ".join(relationships)
    else:
        ficPieces["character_heading"] = "Characters:"

    if characters:
        characters = list(map(lambda x: x.string, characters.find_all("a")))
        if len(characters) > 4:
            ficPieces["characters"] = ", ".join(characters[:4]) + "…"
        else:
            ficPieces["characters"] = ", ".join(characters)

    if freeform: # same as tags
        freeform = list(map(lambda x: x.string, freeform.find_all("a")))
        if len(freeform) > 5:
            ficPieces["tags"] = ", ".join(freeform[:5]) + "…"
        else:
            ficPieces["tags"] = ", ".join(freeform)

    return ficPieces

def makeEmbed(ficPieces):
    words_kudos_bookmarks = f"""
        {ficPieces["words"]} **words**
        {ficPieces["kudos"]} **kudos**
        {ficPieces["bookmarks"]} **bookmarks**
    """

    if "rating" in ficPieces:
        rating = ficPieces["rating"]
    else:
        rating = ""

    if "category" in ficPieces:
        category = ficPieces["category"]
        if len(category.split()) > 1:
            category = "Multi"
    else:
        category = ""

    embed = discord.Embed(
        title = ficPieces["title"],
        description = ficPieces["author"],
        color = ratingColors[rating]
    )

    if "fandoms" in ficPieces:
        embed.add_field(name="Fandoms:", value=ficPieces["fandoms"], inline=False)
    if "summary" in ficPieces:
        embed.add_field(name="Summary:", value=ficPieces["summary"], inline=False)
    if "series" in ficPieces:  
        embed.add_field(name="Series:", value=ficPieces["series"], inline=False)

    if rating:
        embed.add_field(name="Rating:", value=f"{ratingEmoji[rating]} {rating}")
    if "chapters" in ficPieces:
        embed.add_field(name="Chapters:", value=ficPieces["chapters"])
    if "updated" in ficPieces:
        embed.add_field(name=ficPieces["status"], value=datetime.strftime(datetime.strptime(ficPieces["updated"], "%Y-%m-%d"), "%B %d, %Y"))
    
    if "category" in ficPieces:
        embed.add_field(name=f"Category: {ratingEmoji[category]}", value=ficPieces["category"]) 
    if "warnings" in ficPieces:
        embed.add_field(name="Warnings:", value=ficPieces["warnings"])

    embed.add_field(name="Stats:", value=words_kudos_bookmarks)

    if "relationships" in ficPieces:
        embed.add_field(name="Relationships:", value=ficPieces["relationships"], inline=False)
    if "characters" in ficPieces:
        embed.add_field(name=ficPieces["character_heading"], value=ficPieces["characters"], inline=False)
    if "tags" in ficPieces:
        embed.add_field(name="Tags:", value=ficPieces["tags"], inline=False)

    # embed.add_field(name="\u2800", value=field2, inline=False)

    embed.url = ficPieces["link"]
    embed.set_author(name="Archive of Our Own", icon_url="https://archiveofourown.org/images/ao3_logos/logo_42.png")

    return embed

class embedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("embedBuilder is Ready")

    # Commands
    @commands.command()
    async def sendFic(self, ctx, link):
        print(datetime.now())
        the_stuff = generate_ao3_work_summary(link)
        await ctx.channel.typing()
        print(datetime.now())
        embed = makeEmbed(the_stuff)
        embed.set_footer(text=f"Linked by {ctx.message.author}", icon_url=ctx.message.author.avatar.url)
        await ctx.send(embed=embed)
        print(datetime.now())

async def setup(bot):
    await bot.add_cog(embedBuilder(bot))
