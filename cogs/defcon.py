import disnake
from disnake.ext import commands
import json
import os

STATE_FILE = "defcon_state.json"
CONFIG_FILE = "config.json"

# --- Texte d'explication DEFCON ---
DEFCON_EXPLAIN = {
    5: {
        "title": "DEFCON 5 — Opérations normales",
        "desc": "Tous les services fonctionnent normalement. Surveillance standard (Icinga2, alertes)."
    },
    4: {
        "title": "DEFCON 4 — Surveillance renforcée",
        "desc": "Anomalies détectées (charge, petits ralentissements). Pas d'impact client majeur. Équipe en veille."
    },
    3: {
        "title": "DEFCON 3 — Incident en cours",
        "desc": "Incident limité affectant certains clients ou services. Mitigation en cours. Communication interne."
    },
    2: {
        "title": "DEFCON 2 — Incident critique",
        "desc": "Services critiques affectés. Impact client significatif. Mobilisation totale. Communication publique."
    },
    1: {
        "title": "DEFCON 1 — Crise majeure",
        "desc": "Panne massive / attaque grave. Tous les clients impactés. PRA/PCA activés. Communication continue."
    }
}

def load_json(path, default):
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


class DefconView(disnake.ui.View):
    """Buttons publics + admin"""
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    # Admin buttons (visible mais permission checked via decorator in command)
    @disnake.ui.button(label="DEFCON 5", style=disnake.ButtonStyle.success, custom_id="defcon_set_5")
    async def set_5(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.cog.handle_set_button(inter, 5)

    @disnake.ui.button(label="DEFCON 4", style=disnake.ButtonStyle.success, custom_id="defcon_set_4")
    async def set_4(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.cog.handle_set_button(inter, 4)

    @disnake.ui.button(label="DEFCON 3", style=disnake.ButtonStyle.primary, custom_id="defcon_set_3")
    async def set_3(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.cog.handle_set_button(inter, 3)

    @disnake.ui.button(label="DEFCON 2", style=disnake.ButtonStyle.danger, custom_id="defcon_set_2")
    async def set_2(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.cog.handle_set_button(inter, 2)

    @disnake.ui.button(label="DEFCON 1", style=disnake.ButtonStyle.danger, custom_id="defcon_set_1")
    async def set_1(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        await self.cog.handle_set_button(inter, 1)

    # Public button (moved to the end)
    @disnake.ui.button(label="Plus d'infos", style=disnake.ButtonStyle.primary, custom_id="defcon_info")
    async def more_info(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        level = self.cog.state.get("level", 5)
        info = DEFCON_EXPLAIN.get(level, {})
        embed = disnake.Embed(title=info.get("title", f"DEFCON {level}"),
                               description=info.get("desc", ""),
                               color=0x2F3136)
        embed.set_footer(text="DEFCON = DayHosting Emergency Framework for CONtinuity")
        await inter.response.send_message(embed=embed, ephemeral=True)


class Defcon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_json(CONFIG_FILE, {})
        self.channel_name = self.config.get("defcon_channel_name", "『💼』test")
        self.notify_roles = {int(k): int(v) for k,v in self.config.get("notify_roles", {}).items()}
        self.state = load_json(STATE_FILE, {"level": 5, "message_id": None, "channel_id": None})
        self.view = None
        

    def build_embed(self, level: int) -> disnake.Embed:
        info = DEFCON_EXPLAIN.get(level, {})
        color_map = {5:0x2ECC71, 4:0x9B59B6, 3:0xF1C40F, 2:0xE67E22, 1:0xE74C3C}
        emb = disnake.Embed(title=info.get("title", f"DEFCON {level}"),
                            description=info.get("desc", ""),
                            color=color_map.get(level, 0x2F3136))
        emb.set_footer(text="DEFCON = DayHosting Emergency Framework for CONtinuity")
        emb.add_field(name="Niveau actuel", value=f"**DEFCON {level}**", inline=True)
        return emb

    async def set_level(self, guild, level: int, actor=None, source="command"):
        old = self.state.get("level", 5)
        self.state["level"] = level
        save_json(STATE_FILE, self.state)

        # Channel
        channel = disnake.utils.get(guild.text_channels, name=self.channel_name)
        if not channel:
            channel = await guild.create_text_channel(self.channel_name)

        # Embed
        embed = self.build_embed(level)
        content = ""
        role_id = self.notify_roles.get(level)
        if role_id:
            content = f"<@&{role_id}>"

        msg = None
        if self.state.get("message_id"):
            try:
                msg = await channel.fetch_message(self.state["message_id"])
                await msg.edit(content=content, embed=embed, view=self.view if self.view else None)
            except Exception:
                msg = None
        if not msg:
            sent = await channel.send(content=content, embed=embed, view=self.view if self.view else None)
            self.state["message_id"] = sent.id
            save_json(STATE_FILE, self.state)

        # Send DM notifications if level changed and role is configured
        if old != level and role_id:
            try:
                role = guild.get_role(role_id)
                if role:
                    embed = self.build_embed(level)
                    embed.title = f"🚨 DEFCON {level} — Alerte"
                    embed.description = f"Le niveau DEFCON est passé de {old} à {level}.\n\n{embed.description}"

                    # Send DM to all members with the role
                    for member in role.members:
                        try:
                            await member.send(embed=embed)
                        except Exception:
                            # User has DMs disabled or other error, skip
                            pass
            except Exception:
                # Error getting role or sending DMs, skip
                pass

        # Short log
        actor_txt = f" par {actor.mention}" if actor else ""
        await channel.send(f"🔔 DEFCON changé : {old} → {level}{actor_txt} (source: {source})", delete_after=30)

    # Commandes admin
    @commands.command(name="defcon_set", description="Définir le niveau DEFCON (admin only)")
    @commands.has_permissions(administrator=True)
    async def cmd_defcon_set(self, ctx, level: int):
        # Supprimer la commande tapée
        await ctx.message.delete()
        if level <1 or level>5:
            await ctx.send("❌ Le niveau doit être entre 1 et 5.", ephemeral=True)
            return
        await self.set_level(ctx.guild, level, actor=ctx.author, source="command")
        await ctx.send(f"✅ DEFCON réglé à {level}.", ephemeral=True, delete_after=10)

    @commands.command(name="defcon_status", description="Affiche le niveau DEFCON actuel")
    async def cmd_defcon_status(self, ctx):
        level = self.state.get("level",5)
        embed = self.build_embed(level)
        await ctx.send(embed=embed, view=self.view if self.view else None)

    @commands.command(name="defcon_info", description="Explication complète des niveaux")
    async def cmd_defcon_info(self, ctx):
        e = disnake.Embed(title="DEFCON — DayHosting Emergency Framework for CONtinuity",
                          description="Explication des niveaux et procédures associées.")
        for lvl in sorted(DEFCON_EXPLAIN.keys(), reverse=True):
            info = DEFCON_EXPLAIN[lvl]
            e.add_field(name=f"DEFCON {lvl} — {info['title']}", value=info["desc"], inline=False)
        await ctx.send(embed=e)

    @commands.command(name="defcon_init", description="Initialise le message DEFCON")
    @commands.has_permissions(administrator=True)
    async def cmd_defcon_init(self, ctx):
        await self.set_level(ctx.guild, self.state.get("level",5), actor=ctx.author, source="init")
        await ctx.send("✅ Message DEFCON initialisé/actualisé.", delete_after=10)

    # Button handler
    async def handle_set_button(self, inter, level: int):
        # Only admins
        if not inter.author.guild_permissions.administrator:
            await inter.edit_original_response(content="❌ Vous n'avez pas la permission.", ephemeral=True)
            return
        await self.set_level(inter.guild, level, actor=inter.author, source="button")
        await inter.edit_original_response(content=f"✅ DEFCON réglé à {level}.", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        # Initialize the view now that we have an event loop
        self.view = DefconView(self)
        for guild in self.bot.guilds:
            message_id = self.state.get("message_id")
            if message_id:
                try:
                    channel = disnake.utils.get(guild.text_channels, name=self.channel_name)
                    if channel:
                        await channel.fetch_message(message_id)
                except:
                    await self.set_level(guild, self.state.get("level",5), actor=None, source="startup")


def setup(bot: commands.Bot):
    bot.add_cog(Defcon(bot))
    print("Defcon cog loaded")

def teardown(bot):
    bot.remove_cog("Defcon")
    print("Defcon cog unloaded")
