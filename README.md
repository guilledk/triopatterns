# triopatterns

Useful abstractions for ![trio](https://github.com/python-trio/trio)

#### AsyncQueue

This data structure expands upon `trio.SendChannel` & `trio.ReceiveChannel`, it creates a tree-like structure of `AsyncQueue`s, begining with a root queue you can create "subscriber" or "modifier" queues that match and relay messages sent.

I find this structure specially useful for implementing remote bidirectional communication protocols, for example ![boxer](https://github.com/guilledk/boxer)

Or if you just want to check the API:

```python
from triopatterns import AsyncQueue

inbound = AsyncQueue()
```

Anywere in your program create a subscriber:

```python
def matcher(*args):
    return b"hello" in args[0]

# msg_queue will receive all messages that contain the byte sequence "hello"
async with inbound.subscribe(matcher) as msg_queue:
    msg = await msg_queue.receive()
```

Send a message through:

```python
await inbound.send(b"hello world!")
```

You can also use lambdas for subscriber matcher callbacks:

```python
async with inbound.subscribe(
    lambda *args: b"hello" in args[0]
        ) as msg_queue:
    msg = await msg_queue.receive()
```

To match a specific message you can pass more information to the matcher
```python
def matcher(*args):
    return args[0] == args[1]

async with inbound.subscribe(
    matcher,
    args=[b"7"]
        ) as msg_queue:
    msg = await msg_queue.receive()
```

In the case you need to apply a modification to every message sent when matched, use modifiers:

```python
def str_matcher(*args):
    try:
        return (True, str(args[0]))
    except UnicodeDecodeError:
        return (False, None)

async with inbound.modify(str_matcher) as msg_queue:
    # msg will be of type str
    msg = await msg_queue.receive()
```

#### SessionIDManager

Just a really simple class for giving out incremental ids.