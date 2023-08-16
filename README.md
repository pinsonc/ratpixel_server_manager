# RatPixel Server Manager

## What this actually does

Gives a Discord bot commands to start and stop an EC2 server.

## config.py

You need to have a config file in the following format

```
config = {
    "discord_secret": "<token>",
    "server_id": <discord_server_id>,
    "mc_id": "<ec2_instance_id>"
}
```