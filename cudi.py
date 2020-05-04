import discord

from functools import wraps
import random
import os, re

from cal import Reminder


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

        self._calendars = {}

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
        async def send(*, msg, channel_name):
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
                return True
        
        return False

    async def _no(self, message):
        await message.channel.send('fuck u say ?')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # case 1: boss says what
        if (
            isinstance(message.channel, discord.DMChannel) and
            message.author.id == self._owner_id
        ):
            if await self._do_command(message):
                return

        # case 2: consulting privately
        if isinstance(message.channel, discord.DMChannel):
            
            # remind me of class
            if 'remind' in message.content:
                match = re.search(
                    r'((MAA|CSE|MIE|ECO|PHY)[0-9]{3})',
                    message.content,
                )

                if not match:
                    await self._no(message)
                    return

                ccode = match.group(0)

                # create user's calendar
                if message.author.id not in self._calendars:
                    await message.channel.send(
                        'I need your synapses ical link !')
                    return

                # create remind task
                cal = self._calendars[message.author.id]
                cal.remindme(ccode)

                await message.channel.send(
                    f'will remind you of {ccode}')

            if 'calendar/ical' in message.content:
                async with message.channel.typing():
                    match = re.search(
                        r'https://[^\s]+',
                        message.content,
                    )

                    if not match:
                        await self._no(message)
                        return

                    url = match.group(0)
                    reminder = await Reminder.from_link(
                        message.author, url)
                    self._calendars[message.author.id] = reminder

                    await message.channel.send(
                        'your calendar is in my mind ;)')

            if 'next class' in message.content:
                if message.author.id not in self._calendars:
                    await _no(message)
                    return

                reminder = self._calendars[message.author.id]
                msg = next(iter(reminder.listme()))
                await message.channel.send(msg)

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
