import disnake, json
from disnake.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.command(name="help", description="Help command")
    @commands.has_permissions(administrator=True)
    async def send_bot_help(self, ctx, *, command=None):
        """Shows help about a command."""
        # If no command is specified, we're going to show a list of all available commands.
        if command is None:
            embed = disnake.Embed(title="Help", description="List of commands", color=disnake.Color.blue())
            for cog in self.bot.cogs.values():
                commands_desc = ''
                for cmd in cog.get_commands():
                    if cmd.hidden:
                        continue
                    commands_desc += f'{cmd.name} - {cmd.description}\n'
                if commands_desc == '':
                    continue
                embed.add_field(name=cog.qualified_name, value=commands_desc, inline=False)
            await ctx.send(embed=embed)
        else:
            # If a command is specified, we're going to show some specific information about it.
            if (command := self.bot.get_command(command)) is not None:
                embed = disnake.Embed(title=f"Help - {command.name}", description=command.description,
                                      color=disnake.Color.blue())
                embed.add_field(name="Usage", value=command.usage)
                await ctx.send(embed=embed)
            else:
                await ctx.send("That command does not exist.")

def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))
    print("Help cog is loaded")

def teardown(bot):
    bot.remove_cog("Help")
    print("Help cog is unloaded")
