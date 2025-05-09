import disnake
import json
from disnake.ext import commands
import asyncio

class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.command(name="ban", description="Commande pour bannir un utilisateur")
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, member: disnake.Member, *, reason="Aucune raison fournie"):
        if member.guild_permissions.administrator:
            await ctx.send("Erreur : Vous ne pouvez pas bannir un administrateur.")
            return
        await member.send(f"Vous avez été banni de DayHosting par {ctx.author.name} pour la raison suivante : {reason}. Si vous souhaitez contester le bannissement, veuillez nous envoyer un email à contact@dayhosting.fr. Nous vous souhaitons une bonne continuation, Cordialement, l'équipe de DayHosting.fr.")
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni. Raison : {reason}")

    @commands.command(name="unban", description="Commande pour débannir un utilisateur")
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, id: int):
        user = await self.bot.fetch_user(id)
        await ctx.guild.unban(user)
        await ctx.send(f"{user.mention} a été débanni.")

    @commands.command(name="tempban", description="Commande pour bannir temporairement un utilisateur")
    @commands.has_permissions(administrator=True)
    async def tempban(self, ctx, member: disnake.Member, time: int, *, reason="Aucune raison fournie"):
        if member.guild_permissions.administrator:
            await ctx.send("Erreur : Vous ne pouvez pas bannir temporairement un administrateur.")
            return
        await member.send(f"Vous avez été temporairement banni de DayHosting par {ctx.author.name} pour la raison suivante : {reason}, pour une durée de {time} secondes. Si vous souhaitez contester le bannissement, veuillez nous envoyer un email à contact@dayhosting.fr. Nous vous souhaitons une bonne continuation, Cordialement, l'équipe de DayHosting.fr.")
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été temporairement banni pour {time} secondes pour {reason}")
        await asyncio.sleep(time)
        await member.unban(reason="Le temps de bannissement temporaire est terminé.")
        await ctx.send(f"{member.mention} n'est plus banni.")

def setup(bot: commands.Bot):
    bot.add_cog(Ban(bot))
    print("Ban cog is loaded")

def teardown(bot):
    bot.remove_cog("Ban")
    print("Ban cog is unloaded")