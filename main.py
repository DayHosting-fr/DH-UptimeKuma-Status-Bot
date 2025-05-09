import disnake, os, json
from disnake.ext import commands

intents = disnake.Intents.all()

with open('config.json') as f:
    configs = json.load(f)

activity = disnake.Activity(
    name=configs["ACTIVITY_NAME"],
    type=disnake.ActivityType.watching
)

bot = commands.Bot(
    command_prefix=configs["COMMAND_PREFIX"],
    intents=intents,
    activity=activity)
bot.help_command = None
# Loading Cogs for the first time
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

# Here is all the command for admins to load, unload and reload cogs
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    bot.reload_extension(f'cogs.{extension}')
    await ctx.message.delete()
    await ctx.send(f'{extension} reloaded', delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.message.delete()
    await ctx.send(f'{extension} loaded', delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.message.delete()
    await ctx.send(f'{extension} unloaded', delete_after=5)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
bot.run(configs["DISCORD_BOT_TOKEN"])