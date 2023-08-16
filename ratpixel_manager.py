import discord
from discord import app_commands
from discord.ext.commands import has_permissions, CheckFailure
import boto3
from botocore.exceptions import ClientError
import config as CONFIG

discord_secret = CONFIG.config['discord_secret']
minecraft_server_id = CONFIG.config['mc_id']
rat_pile_discord_id = CONFIG.config['server_id']

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

ec2 = boto3.client('ec2', region_name='us-east-1')

@tree.command(name="minecraft_status", description="Reports whether the underlying Minecraft server is online.", guild=discord.Object(id=rat_pile_discord_id))
async def mc_status(interaction):
    response = ec2.describe_instance_status(InstanceIds=[minecraft_server_id])
    if response['InstanceStatuses']:
        await interaction.response.send_message(f"The Minecraft server is running.")
    else:
        await interaction.response.send_message("The Minecraft server is not running.")

@tree.command(name="minecraft_start", description="Starts the Minecraft server.", guild=discord.Object(id=rat_pile_discord_id))
async def mc_start(interaction):
    if not interaction.permissions.administrator:
        response = ec2.describe_instance_status(InstanceIds=[minecraft_server_id])
        if not response['InstanceStatuses']:
            try:
                ec2.start_instances(InstanceIds=[minecraft_server_id], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            try:
                response = ec2.start_instances(InstanceIds=[minecraft_server_id], DryRun=False)
                print(response)
                await interaction.response.send_message(f'The Minecraft server is now being started.')
            except ClientError as e:
                await interaction.response.send_message(f'The starting process encountered an error: {e}')
        else:
            await interaction.response.send_message('The server is already started or is in the process of starting.')
    else:
        await interaction.response.send_message(f'This command can only be executed by server admins.')

@tree.command(name="minecraft_stop", description="Stops the Minecraft server.", guild=discord.Object(id=rat_pile_discord_id))
async def mc_stop(interaction):
    if interaction.permissions.administrator:
        response = ec2.describe_instance_status(InstanceIds=[minecraft_server_id])
        if response['InstanceStatuses']:
            try:
                ec2.stop_instances(InstanceIds=[minecraft_server_id], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            try:
                response = ec2.stop_instances(InstanceIds=[minecraft_server_id], DryRun=False)
                print(response)
                await interaction.response.send_message(f'The Minecraft server is now being stopped.')
            except ClientError as e:
                await interaction.response.send_message(f'The stopping process encountered an error: {e}')
        else:
            await interaction.response.send_message('The server is already stopped.')
    else:
        await interaction.response.send_message(f'This command can only be executed by server admins.')

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=rat_pile_discord_id))
    print(f'We have logged in as {client.user}')

client.run(discord_secret)