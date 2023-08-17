import discord
from discord import app_commands
import boto3
from botocore.exceptions import ClientError
import config as CONFIG

discord_secret = CONFIG.config['discord_secret']
minecraft_server_id = CONFIG.config['mc_id']
rat_pile_discord_id = CONFIG.config['server_id']
terraria_server_id = CONFIG.config['terraria_id']

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

ec2 = boto3.client('ec2', region_name='us-east-1')

@tree.command(name="server_status", description="Reports whether the underlying game server is online.", guild=discord.Object(id=rat_pile_discord_id))
@tree.choices(games=[
    app_commands.Choice(name="Terraria", value=1),
    app_commands.Choice(name="Minecraft", value=2)
])
async def mc_status(interaction, games: app_commands.Choice[int]):
    if games.name == "Minecraft":
            id = minecraft_server_id
    elif games.name == "Terraria":
        id = terraria_server_id
    response = ec2.describe_instance_status(InstanceIds=[id])
    if response['InstanceStatuses']:
        await interaction.response.send_message(f"The Minecraft server is running.")
    else:
        await interaction.response.send_message("The Minecraft server is not running.")

@tree.command(name="server_start", description="Starts the specified server.", guild=discord.Object(id=rat_pile_discord_id))
@tree.choices(games=[
    app_commands.Choice(name="Terraria", value=1),
    app_commands.Choice(name="Minecraft", value=2)
])
async def mc_start(interaction, games: app_commands.Choice[int]):
    if interaction.permissions.administrator:
        if games.name == "Minecraft":
            id = minecraft_server_id
        elif games.name == "Terraria":
            id = terraria_server_id
        response = ec2.describe_instance_status(InstanceIds=[id])
        if not response['InstanceStatuses']:
            try:
                ec2.start_instances(InstanceIds=[id], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            try:
                response = ec2.start_instances(InstanceIds=[id], DryRun=False)
                print(response)
                await interaction.response.send_message(f'The {games.name} server is now being started.')
            except ClientError as e:
                await interaction.response.send_message(f'The starting process encountered an error: {e}')
        else:
            await interaction.response.send_message('The server is already started or is in the process of starting.')
    else:
        await interaction.response.send_message('This command can only be executed by server admins.')

@tree.command(name="server_stop", description="Stops the specified server.", guild=discord.Object(id=rat_pile_discord_id))
@tree.choices(games=[
    app_commands.Choice(name="Terraria", value=1),
    app_commands.Choice(name="Minecraft", value=2)
])
async def mc_stop(interaction, games: app_commands.Choice[int]):
    if interaction.permissions.administrator:
        if games.name == "Minecraft":
            id = minecraft_server_id
        elif games.name == "Terraria":
            id = terraria_server_id
        response = ec2.describe_instance_status(InstanceIds=[id])
        if response['InstanceStatuses']:
            try:
                ec2.stop_instances(InstanceIds=[id], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            try:
                response = ec2.stop_instances(InstanceIds=[id], DryRun=False)
                print(response)
                await interaction.response.send_message(f'The {games.name} server is now being stopped.')
            except ClientError as e:
                await interaction.response.send_message('The stopping process encountered an error: {e}')
        else:
            await interaction.response.send_message('The server is already stopped.')
    else:
        await interaction.response.send_message('This command can only be executed by server admins.')

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=rat_pile_discord_id))
    print(f'We have logged in as {client.user}')

client.run(discord_secret)