#!/usr/bin/env python3


class SessionIDManager:

    def __init__(
        self,
        prefix: str = "",
        subfix: str = "",
        start: int = 0,
        step: int = 1
            ):

        self.prefix = prefix
        self.subfix = subfix
        self.step = step
        self.start = start

        self.last_id = None

    def getid(self) -> str:
        if self.last_id is None:
            self.last_id = self.start

        else:
            self.last_id += self.step

        return f"{self.prefix}{self.last_id}{self.subfix}"
