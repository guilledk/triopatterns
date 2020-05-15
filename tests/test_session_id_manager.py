#!/usr/bin/env python3

from triopatterns import SessionIDManager


async def test_get_id(nursery):

    idmngr = SessionIDManager(
        prefix="prefix-",
        subfix=".subfix",
        step=512
        )

    for i in range(10):
        assert idmngr.getid() == f"prefix-{i * idmngr.step}.subfix"
