import aiohttp
from disnake.ext import commands, tasks
from datetime import datetime

class Hearthbeat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()  # session persistante
        self.hearthbeat_task.start()

    def cog_unload(self):
        self.hearthbeat_task.cancel()
        self.bot.loop.create_task(self.session.close())  # fermeture propre

    @tasks.loop(seconds=60)
    async def hearthbeat_task(self):
        base_url = "https://status.dayhosting.fr/api/push/EMOq149xEc0RaPjDwUOE3xIxUY4TJ1Ee"
        ping = round(self.bot.latency * 1000)

        params = {
            "status": "up",
            "msg": "OK",
            "ping": ping
        }

        try:
            async with self.session.get(base_url, params=params) as response:
                if response.status == 200:
                    print(f"[{datetime.now()}] Heartbeat sent successfully. Ping: {ping}ms.")
                else:
                    text = await response.text()
                    print(f"[{datetime.now()}] Failed to send heartbeat. Status: {response.status}, Response: {text}")

        except aiohttp.ClientError as e:
            print(f"[{datetime.now()}] Heartbeat error: {e}")

    @hearthbeat_task.before_loop
    async def before_hearthbeat_task(self):
        await self.bot.wait_until_ready()
