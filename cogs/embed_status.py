import disnake, socketio, json
from disnake.ext import commands, tasks
from datetime import datetime
from uptime_kuma_api import UptimeKumaApi, MonitorStatus
from uptime_kuma_api.exceptions import UptimeKumaException, Timeout

class Embed_Status(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = None
        self.message = None

        # Chargement de la config
        with open('config.json') as f:
            self.configs = json.load(f)

        # Initialisation de l'API UptimeKuma
        self.setup_api()

        # Démarrage du loop
        self.auto_send_embed.start()

    def cog_unload(self):
        # Fermeture du loop et déconnexion propre
        self.auto_send_embed.cancel()
        if self.api:
            try:
                self.api.logout()
            except Exception as e:
                print(f"Error during UptimeKuma logout: {e}")

    def setup_api(self):
        try:
            self.api = UptimeKumaApi(self.configs["UPTIME_KUMA_SERVER"])
            self.api.login(self.configs["UPTIME_KUMA_USERNAME"], self.configs["UPTIME_KUMA_PASSWORD"])
        except Exception as e:
            print(f"Failed to initialize UptimeKuma API: {e}")
            self.api = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.channel = self.bot.get_channel(self.configs["CHANNEL_ID"])
        if not self.channel:
            print(f"Could not find channel with ID {self.configs['CHANNEL_ID']}")
            return

        # Récupération du message existant ou création
        try:
            with open("message_id.txt", "r") as file:
                message_id = int(file.read())
                self.message = await self.channel.fetch_message(message_id)
        except (FileNotFoundError, disnake.NotFound):
            embed = await self.create_embed()
            self.message = await self.channel.send(embed=embed)
            with open("message_id.txt", "w") as file:
                file.write(str(self.message.id))

    async def create_embed(self):
        embed = disnake.Embed(
            title='Status des serveurs',
            description='Les status sont actualisés toutes les 60 secondes. Version web disponible [ici](https://status.dayhosting.fr)\n',
            color=disnake.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=self.configs["THUMBNAIL_URL"])
        embed.set_author(
            name=self.configs["AUTHOR_NAME"],
            url=self.configs["AUTHOR_URL"],
            icon_url=self.configs["AUTHOR_ICON"]
        )
        embed.set_footer(text='Dernière actualisation des données')

        if not self.api:
            embed.color = disnake.Color.red()
            embed.description = "Impossible de se connecter à Uptime Kuma pour le moment."
            return embed

        try:
            data = self.api.get_status_page(self.configs["UPTIME_KUMA_STATUS_PAGE"])

            # Gestion des maintenances
            maintenances = []
            for maintenance in data.get('maintenanceList', []):
                maintenance_id = maintenance["id"]
                maintenance_data = self.api.get_monitor_maintenance(maintenance_id)
                monitors_list = [m['id'] for m in maintenance_data]
                maintenances.append({
                    'id': maintenance_id,
                    'title': maintenance['title'],
                    'description': maintenance['description'],
                    'monitors': monitors_list
                })

            # Création des champs du embed
            for group in data.get('publicGroupList', []):
                if group['name'] in self.configs.get("EXCLUDED_CATEGORIES", []):
                    continue

                embed_value = ""
                for monitor in group.get('monitorList', []):
                    server_id = monitor['id']
                    server_name = monitor['name']

                    # Vérifie si en maintenance
                    maintenance_status = ""
                    is_in_maintenance = False
                    for m in maintenances:
                        if server_id in m['monitors']:
                            maintenance_status = f"\n__Raison__ :\n `{m['title']}`\n__Description__ :\n `{m['description']}`"
                            is_in_maintenance = True
                            break

                    if is_in_maintenance:
                        server_status_icon = self.configs["STATUS_ICONS"]["MAINTENANCE"]
                    else:
                        try:
                            status_id = self.api.get_monitor_status(server_id)
                            if status_id == MonitorStatus.UP:
                                server_status_icon = self.configs["STATUS_ICONS"]["UP"]
                            elif status_id == MonitorStatus.DOWN:
                                server_status_icon = self.configs["STATUS_ICONS"]["DOWN"]
                            elif status_id == MonitorStatus.PENDING:
                                server_status_icon = self.configs["STATUS_ICONS"]["DEGRADED"]
                            else:
                                server_status_icon = self.configs["STATUS_ICONS"]["UNKNOWN"]
                        except Exception:
                            server_status_icon = self.configs["STATUS_ICONS"]["UNKNOWN"]

                    embed_value += f"{server_status_icon} - {server_name}{maintenance_status}\n"

                if embed_value:
                    embed.add_field(name=group['name'], value=embed_value, inline=False)

            legend = (
                f"{self.configs['STATUS_ICONS']['UP']} - Serveur en ligne\n"
                f"{self.configs['STATUS_ICONS']['DEGRADED']} - Serveur en attente\n"
                f"{self.configs['STATUS_ICONS']['DOWN']} - Serveur hors ligne\n"
                f"{self.configs['STATUS_ICONS']['MAINTENANCE']} - Serveur en maintenance"
            )
            embed.add_field(name="Légende:", value=legend, inline=False)

        except (UptimeKumaException, Timeout, socketio.exceptions.TimeoutError) as e:
            print(f"Erreur UptimeKuma: {e}")
            embed.color = disnake.Color.red()
            embed.description = "Une erreur est survenue avec la connexion au serveur de status. Merci de patienter."

        print(f"Embed updated at {datetime.now()}")
        return embed

    @tasks.loop(seconds=60)
    async def auto_send_embed(self):
        if not self.message:
            return
        embed = await self.create_embed()
        await self.message.edit(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Embed_Status(bot))
    print("Embed_Status cog is loaded")

def teardown(bot):
    bot.remove_cog("Embed_Status")
    print("Embed_Status cog is unloaded")
