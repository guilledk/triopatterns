#!/usr/bin/env python3

import trio

from triopatterns import AsyncQueue


async def main():

    async with trio.open_nursery() as nursery:

        main_queue = AsyncQueue()
        sec_queue = main_queue

        async def _bg_send():
            await main_queue.send("test")

        nursery.start_soon(_bg_send)

        print(await sec_queue.receive())


try:
    trio.run(main)
except KeyboardInterrupt:
    pass