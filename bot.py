import discord

from functools import wraps
import random
import os, re


class Cudi(discord.Client):

    # 227044840309784576
    def __init__(self, owner_id, message_folder, *args, **kws):
        super().__init__(*args, **kws)

        self._owner_id = owner_id
        self._allowed_channels = {}
        self._messages = []

        for mfile in os.listdir(message_folder):
            fname = os.path.join(message_folder, mfile)
            self._messages.append(open(fname).read())

    async def on_ready(self):

        # inelegant way of finding channels on which we can send
        # messages. attempted to use `permissions_for` methods with no
        # success :(k
        for channel in self.get_all_channels():
            if not isinstance(channel, discord.TextChannel):
                continue

            try:
                msg = await channel.send('a')
                await msg.delete()
            except:  # skip when not allowed
                pass
            else:
                self._allowed_channels[channel.name] = channel

    async def on_group_join(self, channel, user):
        ...

    async def _do_command(self, message):
        assert message.author.id == self._owner_id

        # some command infrastructure to catch arguments with a
        # regex and act on them with an async function
        # this with automatic dispatching

        commands = {}

        def _(regex):
            pattern = re.compile(regex)

            def decorator(func):
                @wraps(func)
                async def wrapper(msg):
                    match = pattern.match(msg)
                    return await func(**match.groupdict())

                commands[pattern] = wrapper
                return wrapper

            return decorator

        # here we specify all commands

        @_(r'^send\sto\s(?P<channel_name>[^\s]*)\s(?P<msg>.*)$')
        async def send(*, message, channel_name):
            channel = self._allowed_channels[channel_name]
            await channel.send(msg)

        @_(r'^dm\s(?P<user>[^\s]*)\s(?P<msg>.*)$')
        async def dm(*, msg, user):
            for channel in self._allowed_channels.values():
                member = discord.utils.find(
                    lambda m: m.name.startswith(user),
                    channel.guild.members
                )

                if member is not None:
                    break

            if member is None:
                await message.channel.send(f'could not find user {user}')
                return

            if member.dm_channel is None:
                await member.create_dm()

            await member.dm_channel.send(msg)

        @_(r'^edit\susername\s(?P<username>.*)$')
        async def username(*, username):
            await self.user.edit(username=username)

        # and here we dispatch and execute

        msg = message.content
        for pattern, command in commands.items():
            if pattern.match(msg):
                await command(msg)
                break

    async def on_message(self, message):
        if message.author == self.user:
            return

        # case 1: boss says what
        if (
            isinstance(message.channel, discord.DMChannel) and
            message.author.id == self._owner_id
        ):
            await self._do_command(message)
            return

        # case 2: consulting privately
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send('sorry, too hot for you ;)')
            return

        # case 3: public show
        if self.user.mentioned_in(message):
            msg = random.choice(self._messages)
            await message.channel.send(msg)


if __name__ == '__main__':
    import sys


    token, folder = sys.argv[1:]

    cudi = Cudi(227044840309784576, folder)
    cudi.run(token)
