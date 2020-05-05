import discord

from datetime import datetime as dt, timedelta as td
from functools import wraps
import pickle
import random
import os, re

from cal import Reminder


class Cudi(discord.Client):

    # 227044840309784576
    def __init__(self, owner_id, messages, *args, **kws):
        super().__init__(*args, **kws)

        self._owner_id = owner_id
        self._allowed_channels = {}
        self._messages = messages

        self._calendars = {}

    @classmethod
    def from_config(cls, owner, messages, config=None, *args, **kws):
        if config is not None and os.path.exists(config):
            with open(config, 'rb') as f:
                cudi = pickle.load(f)
            assert isinstance(cudi, cls)

            cudi._owner_id = owner
            cudi._messages = messages
            cudi._config = config

            return cudi

        return cls(owner, messages, *args, **kws)

    # the following two methods are necessary because
    # I used inheritance like an IDIOT

    def __getstate__(self):
        return {
            'o': self._owner_id,
            'm': self._messages,
            'c': self._calendars,
        }

    def __setstate__(self, state):
        self._owner_id = state['o']
        self._messages = state['m']
        self._calendars = state['c']

        super().__init__()

        # reinitialize calendars
        for userid, cal in self._calendars.items():
            user = self.get_user(userid)
            cal.reinit_reminds(user)

    async def on_ready(self):
        return

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

    async def _do_private(self, message):
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
            cal.remindme(ccode, message.author)

            await message.channel.send(
                f'will remind you of {ccode} 5 minutes before')

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
                reminder = await Reminder.from_link(url)
                self._calendars[message.author.id] = reminder

                await message.channel.send(
                    'your calendar is in my mind ;)')

            # boast possibilities
            await message.channel.send((
                'you can now ask:\n'
                ' - "next class",\n'
                ' - "classes today",\n'
                ' - "classes tomorrow",\n'
                ' - "remind me next MAA306",'
            ))

        if 'next class' in message.content:
            if message.author.id not in self._calendars:
                await self._no(message)
                return

            reminder = self._calendars[message.author.id]
            msg = next(iter(reminder.listme()))
            await message.channel.send(msg)

        if 'classes' in message.content:
            if message.author.id not in self._calendars:
                await self._no(message)
                return

            if 'today' in message.content:
                date = dt.today().date()
            elif 'tomorrow' in message.content:
                date = (dt.today() + td(days=1)).date()
            else:
                await self._no(message)
                return

            reminder = self._calendars[message.author.id]
            for msg in reminder.listme(date=date):
                await message.channel.send(msg)

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
            await self._do_private(message)
            return

        # case 3: public show
        if self.user.mentioned_in(message):
            msg = random.choice(self._messages)
            await message.channel.send(msg)


if __name__ == '__main__':
    import sys


    # config argument optional
    token, folder, *config = sys.argv[1:]

    # read all messages from files
    messages = []
    for mfile in os.listdir(folder):
        fname = os.path.join(folder, mfile)
        messages.append(open(fname).read())

    cudi = Cudi.from_config(227044840309784576, messages, *config)

    try:
        cudi.run(token)
    except KeyboardInterrupt:
        ...
    finally:
        if config:
            with open(*config, 'wb') as f:
                pickle.dump(cudi, f)
