import discord
import ics

from datetime import datetime as dt
import asyncio
import aiohttp
import random


class Reminder:

    def __init__(self, user, cal, reminds=None):
        # must be called when loop is  active
        self.user = user
        self.cal = cal

        if reminds is None:
            self.reminds = []

        # loop dependent statements
        for event in self.reminds:
            asyncio.create_task(self._remind(event))

    async def _remind(self, event):
        '''long running remind coroutine'''
        # sleep 1 day at a time, maximum
        while (d := event.begin - dt.now(tz=event.begin.tzinfo)) > 0:
            await asyncio.sleep(min(d, 86400))

        if self.user.dm_channel is None:
            await self.user.create_dm()

        msg = random.choice([
            'Ello guvna, go to {n}, {t}',
            'Suckers don\'t miss {n}, {t}',
            'Please don\'t forget {n}, {t}',
        ])

        await self.user.dm_channel.send(
            msg.format(n=event.name, t=event.humanize()))

    @classmethod
    async def from_link(cls, user, link):
        '''create `Reminder` object from ical link'''
        async with aiohttp.ClientSession() as sess:
            async with sess.get(link) as resp:
                text = await resp.text()

        cal = ics.Calendar(text)
        return cls(user, cal)

    def futures(self):
        '''iterator over sorted future events'''

        events = sorted(self.cal.events, key=lambda ev: ev.begin)
        for event in events:

            # do not consider past events
            now = dt.now(tz=event.begin.tzinfo)
            if event.begin < now:
                continue

            yield event

    def listme(self):
        '''list events as messages'''
        for event in self.futures():
            yield f'{event.name}, {event.begin.humanize()}'

    def remindme(self, ccode):
        '''finds event according to course code'''
        for event in self.futures():
            if event.name.lower().startswith(ccode):
                self.reminds.append(event)
                asyncio.create_task(self._remind(event))
