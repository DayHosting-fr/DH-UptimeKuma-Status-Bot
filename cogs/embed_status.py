import disnake, socketio, json
from disnake.ext import commands, tasks
from datetime import datetime
from uptime_kuma_api import UptimeKumaApi
from uptime_kuma_api.exceptions import UptimeKumaException, Timeout

class Embed_Status(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('config.json') as f:
            self.configs = json.load(f)

    @commands.Cog.listener()
    async def on_ready(self):

        # Check if the message ID exists in a file
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
            # If the message ID does not exist or the message does not exist, send a new message
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
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/icons/833439085950664714/bbfb624af1ee9d6b3d2921d82102be0f.png?size=512" # Image du serveur
            )
            embed.set_author(
                name='DayHosting', # Nom de l'auteur
                url='https://dayhosting.fr', # Lien de l'auteur
                icon_url='https://cdn.discordapp.com/icons/833439085950664714/bbfb624af1ee9d6b3d2921d82102be0f.png?size=512' # Image de l'auteur
            )
            embed.set_footer(
                text=f'Dernière actualisation des données'
            )

            data = api.get_status_page("dayhosting")

            if data['maintenanceList'] != []:
                maintenances = []
                monitors_list_maintenance = []
                for i in range(len(data['maintenanceList'])):
                    maintenance_id = data['maintenanceList'][i]["id"]
                    maintenance_data = api.get_monitor_maintenance(maintenance_id)
                    for k in range(len(maintenance_data)):
                        monitors_list_maintenance.append(maintenance_data[k]['id'])
                    maintenances.append({'id': maintenance_id,'title': data['maintenanceList'][i]['title'], 'description':data['maintenanceList'][i]['description'],'monitors':monitors_list_maintenance})



            for i in range(len(data['publicGroupList'])):
                embed_title = data['publicGroupList'][i]['name']
                embed_value = ""
                for n in range(len(data['publicGroupList'][i]['monitorList'])):
                    server_id = data['publicGroupList'][i]['monitorList'][n]['id']
                    server_name = data['publicGroupList'][i]['monitorList'][n]['name']
                    server_status = "<a:warning:1237966536212349010>"
                    maintenance_status = ""
                    get_server_status_id= api.get_monitor_status(server_id).value
                    if get_server_status_id == 0:
                        server_status = "<a:offline:1237966540519768144>"
                    elif get_server_status_id == 1:
                        server_status = "<a:online:1237966542352945192>"
                    elif get_server_status_id == 2:
                        server_status = ":<a:warning:1237966536212349010>"
                    elif get_server_status_id == 3:
                        for l in range(len(maintenances)):
                            if server_id in maintenances[l]['monitors']:
                                maintenance_status = f"\n__Raison__ :\n `{maintenances[l]['title']}`\n__Description__ :\n `{maintenances[l]['description']}`"
                        server_status = "<a:maintenance:1237966537483358228>"
                    embed_value += f"{server_status} - {server_name}{maintenance_status}\n"

                embed.add_field(
                    name=embed_title,
                    value=embed_value,
                    inline=False
                )
            embed.add_field(
                name="Légende:",
                value="<a:online:1237966542352945192> - Serveur en ligne\n<a:warning:1237966536212349010> - Serveur en attente\n<a:offline:1237966540519768144> - Serveur hors ligne\n<a:maintenance:1237966537483358228> - Serveur en maintenance\n",
                inline=False
            )
            api.logout()

        except(UptimeKumaException,Timeout,socketio.exceptions.TimeoutError) as e:
            embed = disnake.Embed(
                title='Status des serveurs',
                description='Une erreur est survenu avec la connexion a notre serveur de status, merci de patienter quelques instants ou de contacter un <@&841787186558926898>.',
                color=disnake.Color.blue(),
                timestamp=datetime.now()
            )
            if api is not None:
                api.logout()
            print(e)


        print(f"Embed updated at {datetime.now()}")

        return embed
    @tasks.loop(seconds=300)
    async def auto_send_embed(self):
        embed = self.create_embed()
        await self.auto_send_embed.message.edit(embed=embed)
def setup(bot: commands.Bot):
    bot.add_cog(Embed_Status(bot))
    print("Embed_Status cog is loaded")

def teardown(bot):
    bot.remove_cog("Embed_Status")
    print("Embed_Status cog is unloaded")