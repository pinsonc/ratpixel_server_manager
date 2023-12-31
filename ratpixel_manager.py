import discord
from discord import app_commands
import boto3
from botocore.exceptions import ClientError
import config as CONFIG
from mcrcon import MCRcon



discord_secret = CONFIG.config['discord_secret']
minecraft_server_id = CONFIG.config['mc_id']
rat_pile_discord_id = CONFIG.config['server_id']
terraria_server_id = CONFIG.config['terraria_id']
rcon_pwd = CONFIG.config['rcon_pwd']
mc_server_ip = CONFIG.config['mc_ip']

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

ec2 = boto3.client('ec2', region_name='us-east-1')
ssm_client = boto3.client('ssm', region_name='us-east-1')

@tree.command(name="server_status", description="Reports whether the underlying game server is online.", guild=discord.Object(id=rat_pile_discord_id))
@app_commands.choices(game=[
    app_commands.Choice(name="Terraria", value=1),
    app_commands.Choice(name="Minecraft", value=2)
])
async def server_status(interaction, game: app_commands.Choice[int]):
    if game.name == "Minecraft":
            id = minecraft_server_id
    elif game.name == "Terraria":
        id = terraria_server_id
    response = ec2.describe_instance_status(InstanceIds=[id])
    if response['InstanceStatuses']:
        await interaction.response.send_message(f"The Minecraft server is running.")
    else:
        await interaction.response.send_message("The Minecraft server is not running.")

@tree.command(name="server_start", description="Starts the specified server.", guild=discord.Object(id=rat_pile_discord_id))
@app_commands.choices(game=[
    app_commands.Choice(name="Terraria", value=1),
    app_commands.Choice(name="Minecraft", value=2)
])
async def server_start(interaction, game: app_commands.Choice[int]):
    if interaction.permissions.administrator:
        if game.name == "Minecraft":
            id = minecraft_server_id
        elif game.name == "Terraria":
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
                await interaction.response.send_message(f'The {game.name} server is now being started.')
            except ClientError as e:
                await interaction.response.send_message(f'The starting process encountered an error: {e}')
        else:
            await interaction.response.send_message('The server is already started or is in the process of starting.')
    else:
        await interaction.response.send_message('This command can only be executed by server admins.')

@tree.command(name="server_stop", description="Stops the specified server.", guild=discord.Object(id=rat_pile_discord_id))
@app_commands.choices(game=[
    app_commands.Choice(name="Terraria", value=1),
    app_commands.Choice(name="Minecraft", value=2)
])
async def server_stop(interaction, game: app_commands.Choice[int]):
    if interaction.permissions.administrator:
        if game.name == "Minecraft":
            id = minecraft_server_id
        elif game.name == "Terraria":
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
                await interaction.response.send_message(f'The {game.name} server is now being stopped.')
            except ClientError as e:
                await interaction.response.send_message('The stopping process encountered an error: {e}')
        else:
            await interaction.response.send_message('The server is already stopped.')
    else:
        await interaction.response.send_message('This command can only be executed by server admins.')

@tree.command(name="minecraft_players_online", description="Lists players currently online in Minecraft.", guild=discord.Object(id=rat_pile_discord_id))
async def minecraft_players(interaction):
    response = ec2.describe_instance_status(InstanceIds=[minecraft_server_id])
    if response["InstanceStatuses"]:
        with MCRcon(mc_server_ip, rcon_pwd) as mcr:
            resp = mcr.command("/list")
            await interaction.response.send_message(f'{resp}')
    else:
        await interaction.response.send_message('The Minecraft server is offline.')

@tree.command(name="minecraft_add_mod", description="Adds the linked mod and restarts the server.", guild=discord.Object(id=rat_pile_discord_id))
@app_commands.describe(mod_id="The 7 digit CurseForge identifier.")
@app_commands.rename(mod_id='download_link')
@app_commands.describe(mod_name="The full filename of the mod (include .jar).")
async def minecraft_players(interaction, mod_id: str, mod_name: str):
    dl_url = f'https://media.forgecdn.net/files/<{int(mod_id[0:4])}>/{int(mod_id[5:])}/{mod_name}'
    response = ssm_client.send_command(
        DocumentName="AWS-RunShellScript", # One of AWS' preconfigured documents
        Parameters={'commands': [
            'sudo su',
            'cd ../../minecraft/mods',
            f'wget {dl_url}',
            'systemctl daemon-reload',
            'systemctl restart minecraft.service'
        ]},
        InstanceIds=[minecraft_server_id],
    )
    await interaction.response.send_message(f'{response}')

@tree.command(name="minecraft_remove_mod", description="Removes the linked mod and restarts the server.", guild=discord.Object(id=rat_pile_discord_id))
@app_commands.describe(mod_name="The full filename of the mod (include .jar).")
async def minecraft_players(interaction, mod_name: str):
    response = ssm_client.send_command(
        DocumentName="AWS-RunShellScript", # One of AWS' preconfigured documents
        Parameters={'commands': [
            'sudo su',
            'cd ../../minecraft/mods',
            f'rm -f {mod_name}',
            'systemctl daemon-reload',
            'systemctl restart minecraft.service'
        ]},
        InstanceIds=[minecraft_server_id],
    )
    await interaction.response.send_message(f'{response}')

@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')

client.run(discord_secret)