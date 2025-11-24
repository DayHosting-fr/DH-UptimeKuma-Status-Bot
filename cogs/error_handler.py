import json, disnake
from disnake.ext import commands

class ErrorHandler(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            try:
                await ctx.message.delete()
            except disnake.Forbidden:
                pass
            await ctx.send("Commande non trouvée. Veuillez vérifier et essayer à nouveau.", delete_after=5)
        elif isinstance(error, commands.MissingRequiredArgument):
            try:
                await ctx.message.delete()
            except disnake.Forbidden:
                pass
            await ctx.send("Il manque un argument requis pour cette commande.", delete_after=5)
        elif isinstance(error, commands.MissingPermissions):
            try:
                await ctx.message.delete()
            except disnake.Forbidden:
                pass
            await ctx.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.", delete_after=5)
        else:
            try:
                await ctx.message.delete()
            except disnake.Forbidden:
                pass
            await ctx.send(f"Une erreur est survenue : {error}", delete_after=15)

def setup(bot: commands.Bot):
    bot.add_cog(ErrorHandler(bot))
    print("ErrorHandler cog is loaded")

def teardown(bot):
    bot.remove_cog("ErrorHandler")
    print("ErrorHandler cog is unloaded")