import json, disnake
from disnake.ext import commands

class UserInfo(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def userinfo(self, ctx, member: disnake.Member = None):
        member = member or ctx.author  # Si aucun membre n'est fourni, utilisez celui qui a envoyé le message
        embed = disnake.Embed(title=f"Informations de l'utilisateur {member.name}", color=disnake.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nom d'utilisateur", value=member.display_name, inline=True)
        embed.add_field(name="Créé le", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
        embed.add_field(name="Rejoint le", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
        embed.add_field(name="Rôles", value=" ".join([role.mention for role in member.roles[1:]]), inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)
def setup(bot: commands.Bot):
    bot.add_cog(UserInfo(bot))
    print("UserInfo cog is loaded")

def teardown(bot):
    bot.remove_cog("UserInfo")
    print("UserInfo cog is unloaded")