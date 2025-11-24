import disnake, socketio, json
from disnake.ext import commands, tasks
from datetime import datetime
from uptime_kuma_api import UptimeKumaApi, MonitorStatus
from uptime_kuma_api.exceptions import UptimeKumaException, Timeout

class Embed_Status(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.channel = self.bot.get_channel(self.configs["CHANNEL_ID"])
        if self.channel is None:
            print(f"Could not find channel with ID {self.configs['CHANNEL_ID']}")
            return
        try:
            with open("message_id.txt", "r") as file:
                message_id = int(file.read())
                message = await self.channel.fetch_message(message_id)
        except (FileNotFoundError, disnake.NotFound):
            embed = self.create_embed()
            message = await self.channel.send(embed=embed)
            with open("message_id.txt", "w") as file:
                file.write(str(message.id))

        self.auto_send_embed.message = message
        self.auto_send_embed.start()

    def create_embed(self):
        api = None
        try:
            api = UptimeKumaApi(self.configs["UPTIME_KUMA_SERVER"])
            api.login(self.configs["UPTIME_KUMA_USERNAME"], self.configs["UPTIME_KUMA_PASSWORD"])

            embed = disnake.Embed(
                title='Status des serveurs',
                description='Les status sur cette page sont actualisés toutes les 60 secondes. Une version web est disponible [ici](https://status.dayhosting.fr)\n',
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

            data = api.get_status_page(self.configs["UPTIME_KUMA_STATUS_PAGE"])

            maintenances = []
            if data.get('maintenanceList'):
                for maintenance in data['maintenanceList']:
                    maintenance_id = maintenance["id"]
                    maintenance_data = api.get_monitor_maintenance(maintenance_id)
                    monitors_list_maintenance = [m['id'] for m in maintenance_data]
                    maintenances.append({
                        'id': maintenance_id,
                        'title': maintenance['title'],
                        'description': maintenance['description'],
                        'monitors': monitors_list_maintenance
                    })

            for group in data['publicGroupList']:
                if group['name'] in self.configs.get("EXCLUDED_CATEGORIES", []):
                    continue

                embed_title = group['name']
                embed_value = ""
                for monitor in group['monitorList']:
                    server_id = monitor['id']
                    server_name = monitor['name']

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
                            status_id = api.get_monitor_status(server_id)
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
                    embed.add_field(name=embed_title, value=embed_value, inline=False)

            legend = (
                f"{self.configs['STATUS_ICONS']['UP']} - Serveur en ligne\n"
                f"{self.configs['STATUS_ICONS']['DEGRADED']} - Serveur en attente\n"
                f"{self.configs['STATUS_ICONS']['DOWN']} - Serveur hors ligne\n"
                f"{self.configs['STATUS_ICONS']['MAINTENANCE']} - Serveur en maintenance"
            )
            embed.add_field(name="Légende:", value=legend, inline=False)

            api.logout()

        except (UptimeKumaException, Timeout, socketio.exceptions.TimeoutError) as e:
            print(e)
            embed = disnake.Embed(
                title='Status des serveurs',
                description='Une erreur est survenue avec la connexion a notre serveur de status, merci de patienter quelques instants ou de contacter un <@&841787186558926898>.',
                color=disnake.Color.red(),
                timestamp=datetime.now()
            )
            if api:
                try:
                    api.logout()
                except Exception as logout_error:
                    print(f"Error during logout: {logout_error}")
            print(e)

        print(f"Embed updated at {datetime.now()}")
        return embed

    @tasks.loop(seconds=60)
    async def auto_send_embed(self):
        embed = self.create_embed()
        await self.auto_send_embed.message.edit(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Embed_Status(bot))
    print("Embed_Status cog is loaded")

def teardown(bot):
    bot.remove_cog("Embed_Status")
    print("Embed_Status cog is unloaded")
