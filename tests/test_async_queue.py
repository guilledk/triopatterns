#!/usr/bin/env python3

from triopatterns import AsyncQueue


async def test_send_sub(nursery):

    root_queue = AsyncQueue()
    packets = []

    for i in range(1000):
        packets.append(b"Hello")
        packets.append("World")

    async def producer():
        for i in range(len(packets)):
            await root_queue.send(packets[i])

    async def bytes_consumer():
        async with root_queue.subscribe(
            lambda *args: isinstance(args[0], bytes),
            history=True
                ) as sub_queue:

            for i in range(len(packets)):
                await sub_queue.receive()

        assert True

    async def str_consumer():
        async with root_queue.subscribe(
            lambda *args: isinstance(args[0], str),
            history=True
                ) as sub_queue:

            for i in range(len(packets)):
                await sub_queue.receive()

        assert True

    nursery.start_soon(producer)
    nursery.start_soon(bytes_consumer)
    nursery.start_soon(str_consumer)


async def test_send_modify(nursery):

    root_queue = AsyncQueue()
    send_amount = 1000000

    async def producer():
        for i in range(send_amount):
            await root_queue.send(b"hello")

    async def consumer():
        async with root_queue.modify(
            lambda *args: (True, str(args[0])),
            history=True
                ) as sub_queue:

            for i in range(send_amount):
                assert (await sub_queue.receive())[1] == "hello"

    nursery.start_soon(producer)
    nursery.start_soon(consumer)


async def test_send_observe(nursery):

    root_queue = AsyncQueue()
    send_amount = 1000000

    async def producer():
        for i in range(send_amount):
            await root_queue.send(None)

    async def consumer():
        async with root_queue.observe(
            history=True
                ) as sub_queue:

            for i in range(send_amount):
                await sub_queue.receive()

        assert True

    nursery.start_soon(producer)

    for i in range(5):
        nursery.start_soon(consumer)


async def test_observe_history(nursery):

    root_queue = AsyncQueue()

    await root_queue.send("This is the first message")
    await root_queue.send("This is the second message")

    async def old_beholder(task_status):
        async with root_queue.observe(history=True) as sub_queue:
            task_status.started()
            assert await sub_queue.receive() == "This is the first message"
            assert await sub_queue.receive() == "This is the second message"
            assert await sub_queue.receive() == "This is the third message"

    await nursery.start(old_beholder)

    async def young_beholder(task_status):
        async with root_queue.observe() as sub_queue:
            task_status.started()
            assert await sub_queue.receive() == "This is the third message"

    await nursery.start(young_beholder)

    await root_queue.send("This is the third message")
