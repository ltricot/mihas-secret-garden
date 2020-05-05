import discord
import ics

from datetime import datetime as dt
import asyncio
import aiohttp
import random


class Reminder:

    def __init__(self, cal, reminds=None):
        self.cal = cal

        if reminds is None:
            self.reminds = {}

    def reinit_reminds(self, user):
        # must be called while loop active
        for ccode, event in self.reminds.items():
            asyncio.create_task(self._remind(ccode, event, user))

    async def _remind(self, ccode, event, user):
        '''long running remind coroutine'''
        # sleep 1 day at a time, maximum
        remaining = lambda: event.begin - dt.now(tz=event.begin.tzinfo)
        while remaining() > 0:
            await asyncio.sleep(min(remaining() - 5 * 60, 86400))

        if user.dm_channel is None:
            await user.create_dm()

        msg = random.choice([
            'Ello guvna, go to {n}, {t}',
            'Suckers don\'t miss {n}, {t}',
            'Please don\'t forget {n}, {t}',
        ])

        await user.dm_channel.send(
            msg.format(n=event.name, t=event.begin.humanize()))

        del self.reminds[ccode]

    @classmethod
    async def from_link(cls, link):
        '''create `Reminder` object from ical link'''
        async with aiohttp.ClientSession() as sess:
            async with sess.get(link) as resp:
                text = await resp.text()

        cal = ics.Calendar(text)
        return cls(cal)

    def futures(self):
        '''iterator over sorted future events'''

        events = sorted(self.cal.events, key=lambda ev: ev.begin)
        for event in events:

            # do not consider past events
            now = dt.now(tz=event.begin.tzinfo)
            if event.begin < now:
                continue

            yield event

    def listme(self, date=None):
        '''list events as messages'''
        for event in self.futures():
            if date is None or event.begin.date() == date:
                yield f'{event.name}, {event.begin.humanize()}'

    def remindme(self, ccode, user):
        '''finds event according to course code'''
        if ccode in self.reminds:
            return False

        for event in self.futures():
            if event.name.lower().startswith(ccode):
                self.reminds[ccode] = event
                asyncio.create_task(self._remind(ccode, event, user))

        return True
