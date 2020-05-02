import discord

import random
import math
import os


client = discord.Client()

commits = []
for fname in os.listdir('MESSAGES'):
    with open(f'MESSAGES/{fname}') as f:
        commits.append(f.read())

@client.event
async def on_ready():
    print('logged in')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if 'miha' in message.content:
        msg = random.choice(commits)
        await message.channel.send(f'{msg}')
        print(f'sent "{msg}"')


if __name__ == '__main__':
    client.run(os.environ['DISCORD_BOT_TOKEN'])
