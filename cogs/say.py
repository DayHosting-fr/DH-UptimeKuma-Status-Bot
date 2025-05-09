import disnake
import json
from disnake.ext import commands
from datetime import datetime

class Say(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.command(name="say", description="Say command")
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, args: str):
        # Parse args to extract title and text
        if "|" in args:
            titre, text = map(str.strip, args.split("|", 1))
        else:
            titre, text = None, args

        # Format the description with the title if provided
        description = f"__**{titre}**__\n\n{text}" if titre else text
        embed = disnake.Embed(
            title="L'équipe DayHosting",
            description=description,
            color=disnake.Colour.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"By {ctx.author.name}")
        await ctx.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Say(bot))
    print("Say cog is loaded")

def teardown(bot):
    bot.remove_cog("Say")
    print("Say cog is unloaded")
