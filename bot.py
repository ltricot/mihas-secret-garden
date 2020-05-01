import discord
import aiohttp

from dataclasses import dataclass, field
from threading import Thread
from typing import List
import asyncio
import random
import math
import os
import re


@dataclass
class Repo:
    user: str
    repo: str
    target: str
    commits: List = field(default_factory=list)

    # weird githb shit in header
    pattern = re.compile(
        r'<.*\?page=([0-9]*)>; rel="next",\s'
        r'<.*\?page=([0-9]*)>; rel="last"'
    )

    def __post_init__(self):
        self.url = (
            f'https://api.github.com/repos/{self.user}'
            f'/{self.repo}/commits'
        )

    async def _commits(self, client):
        '''asynchronous iterator over the target's commits in repository
        https://github.com/{user}/{repo}
        '''

        page, last = 1, math.inf
        while page <= last:
            async with client.get(self.url, params={'page': page}) as resp:
                if resp.status != 200:
                    # rate limited -- wait 5 minutes
                    await asyncio.sleep(60 * 5)

                # paging
                if 'link' in resp.headers:
                    match = self.pattern.match(resp.headers['link'])
                    if not match:
                        continue

                    page = int(match.group(1))
                    last = int(match.group(2))

                jso = await resp.json()
                for commit in jso:
                    author = commit['commit']['author']['email']
                    if author != self.target:
                        continue

                    yield commit

    async def pull(self):
        '''pull the target's commits from https://github.com/{user}/{repo} and
        store them in self.commits'''

        async with aiohttp.ClientSession() as sess:
            async for commit in self._commits(sess):
                self.commits.append(commit)


client = discord.Client()
commits = []

@client.event
async def on_ready():
    def start(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    Thread(target=start, args=(loop,)).start()

    tasks = []
    for repo in os.environ['DISCORD_BOT_REPOS'].split(':'):
        user, repo = repo.split('/')
        puller = Repo(user, repo, 'mihasmaka1@gmail.com', commits)
        loop.call_soon_threadsafe(asyncio.create_task, puller.pull())

    print('logged in')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if 'miha' in message.content:
        commit = random.choice(commits)
        msg = commit['commit']['message']
        await message.channel.send(f'{msg}')
        print(f'sent "{msg}"')


if __name__ == '__main__':
    client.run(os.environ['DISCORD_BOT_TOKEN'])
