#!/usr/bin/env python3

import trio
import math

from contextlib import asynccontextmanager


class AsyncQueue:

    def __init__(self):
        self.inport, self.outport = trio.open_memory_channel(math.inf)
        self.history = []
        self.subs = []  # subscribers match and relay messages
        self.mods = []  # modifiers match, modify and relay messages

    """
    subscriber implementation
    """

    def match_sub(self, sub) -> bool:
        # match each message in history, and if matched save index
        matched_idxs = []
        for msg in self.history[sub["rptr"]:]:
            if sub["match"](msg, *sub["*args"]):
                matched_idxs.append(sub["rptr"])

            sub["rptr"] += 1

        return matched_idxs

    async def sub(self, match_cb, args=[], history=False):
        nsub = {
            "rptr": 0 if history else len(self.history),  # read pointer
            "match": match_cb,  # match callback
            "*args": args,
            "queue": AsyncQueue()
        }
        self.subs.append(nsub)

        # match previous msgs
        matched = self.match_sub(nsub)
        if len(matched) > 0:
            for idx in matched:
                await nsub["queue"].send(self.history[idx])

        return nsub

    def unsub(self, sub):
        self.subs.remove(sub)

    @asynccontextmanager
    async def subscribe(self, matcher, args=[], history=False):
        try:
            sub = await self.sub(
                matcher,
                args=args,
                history=history
                )
            yield sub["queue"]
        finally:
            self.unsub(sub)

    """
    modifier implementation
    """

    def match_mod(self, mod) -> bool:
        # match each message in history, and if matched save index
        matched_idxs = []
        for msg in self.history[mod["rptr"]:]:
            result, modmsg = mod["match"](msg, *mod["*args"])
            if result:
                matched_idxs.append(
                    (mod["rptr"], modmsg)
                    )

            mod["rptr"] += 1

        return matched_idxs

    async def mod(self, match_cb, args=[], history=False):
        nmod = {
            "rptr": 0 if history else len(self.history),
            "match": match_cb,
            "*args": args,
            "queue": AsyncQueue()
        }
        self.mods.append(nmod)

        # match previous msgs
        matched = self.match_mod(nmod)
        if len(matched) > 0:
            for idx, msg in matched:
                await nmod["queue"].send(msg)

        return nmod

    def unmod(self, mod):
        self.mods.remove(mod)

    @asynccontextmanager
    async def modify(self, matcher, args=[], history=False):
        try:
            mod = await self.mod(
                matcher,
                args=args,
                history=history
                )
            yield mod["queue"]
        finally:
            self.unmod(mod)


    @asynccontextmanager
    async def observe(self, history=False):
        try:
            obsv = await self.sub(
                lambda *args: True,
                history=history
                )

            yield obsv["queue"]
        finally:
            self.unsub(obsv)

    """
    send & recv
    """

    async def send(self, msg):

        self.history.append(msg)

        propagated = False

        for sub in self.subs:
            matched = self.match_sub(sub)
            if len(matched) > 0:
                for idx in matched:
                    await sub["queue"].send(self.history[idx])
                propagated = True

        for mod in self.mods:
            matched = self.match_mod(mod)
            if len(matched) > 0:
                for idx, msg in matched:
                    await mod["queue"].send(msg)
                propagated = True

        if not propagated:
            await self.inport.send(msg)

    async def receive(self):
        return await self.outport.receive()


class SessionIDManager:

    def __init__(
        self,
        prefix="",
        subfix="",
        start=0,
        step=1
            ):

        self.prefix = prefix
        self.subfix = subfix
        self.step = step
        self.start = start

        self.last_id = None

    def getid(self):
        if self.last_id is None:
            self.last_id = self.start

        else:
            self.last_id += self.step

        return f"{self.prefix}{self.last_id}{self.subfix}"
