#!/usr/bin/env python3

import trio
import math

from typing import Callable, List, Dict, Any

from contextlib import asynccontextmanager


class AsyncQueue:

    def __init__(self):
        self.inport, self.outport = trio.open_memory_channel(math.inf)
        self.history: List[Any] = []
        self.subs: List[Dict] = []  # subscribers match and relay msgs
        self.mods: List[Dict] = []  # modifiers match, modify and relay msgs
        self.caps: List[Dict] = []  # captors match and caputre msgs

    """
    subscriber implementation
    """

    def match_sub(self, sub: Dict) -> bool:
        # match each message in history, and if matched save index
        matched_idxs = []
        for msg in self.history[sub["rptr"]:]:
            if sub["match"](msg, *sub["*args"]):
                matched_idxs.append(sub["rptr"])

            sub["rptr"] += 1

        return matched_idxs

    async def sub(
        self,
        match_cb: Callable[[List], bool],
        args: List = [],
        history: bool = False
            ):

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
    async def subscribe(
        self,
        matcher: Callable[[List], bool],
        args: List = [],
        history: bool = False
            ):

        sub = None
        try:
            sub = await self.sub(
                matcher,
                args=args,
                history=history
                )
            yield sub["queue"]
        finally:
            if sub:
                self.unsub(sub)

    """
    modifier implementation
    """

    def match_mod(self, mod: Dict) -> bool:
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

    async def mod(
        self,
        match_cb: Callable[[List], bool],
        args: List = [],
        history: bool = False
            ):

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

    def unmod(self, mod: Dict):
        self.mods.remove(mod)

    @asynccontextmanager
    async def modify(
        self,
        matcher: Callable[[List], bool],
        args: List = [],
        history: bool = False
            ):

        mod = None
        try:
            mod = await self.mod(
                matcher,
                args=args,
                history=history
                )
            yield mod["queue"]
        finally:
            if mod:
                self.unmod(mod)

    # observer

    @asynccontextmanager
    async def observe(self, history: bool = False):
        obsv = None
        try:
            obsv = await self.sub(
                lambda *args: True,
                history=history
                )

            yield obsv["queue"]
        finally:
            if obsv:
                self.unsub(obsv)

    """
    captor implementation
    """

    async def cap(
        self,
        match_cb: Callable[[List], bool],
        args: List = []
            ):

        ncap = {
            "match": match_cb,
            "*args": args,
            "queue": AsyncQueue()
        }
        self.caps.append(ncap)

        return ncap

    def uncap(self, cap: Dict):
        self.caps.remove(cap)

    @asynccontextmanager
    async def capture(
        self,
        matcher: Callable[[List], bool],
        args: List = []
            ):

        cap = None
        try:
            cap = await self.cap(
                matcher,
                args=args
                )
            yield cap["queue"]
        finally:
            if cap:
                self.uncap(cap)

    """
    send & recv
    """

    async def send(self, msg: Any) -> None:

        self.history.append(msg)

        # captors
        captured = False

        for cap in self.caps:
            result, capmsg = cap["match"](msg, *cap["*args"])
            if result:
                await cap["queue"].send(capmsg)
                captured = True

        propagated = captured

        # subscribers
        for sub in self.subs:
            if not captured:
                matched = self.match_sub(sub)
                if len(matched) > 0:
                    for idx in matched:
                        await sub["queue"].send(self.history[idx])
                    propagated = True

            else:
                sub["rptr"] += 1

        # modifiers
        for mod in self.mods:
            if not captured:
                matched = self.match_mod(mod)
                if len(matched) > 0:
                    for idx, msg in matched:
                        await mod["queue"].send(msg)
                    propagated = True

            else:
                mod["rptr"] += 1

        if not propagated:
            await self.inport.send(msg)

        return None

    async def receive(self) -> Any:
        return await self.outport.receive()
