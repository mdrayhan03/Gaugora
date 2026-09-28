"""Channel protocol definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChannelMessage:
    subject: str
    body: str
    to_addresses: list[str]


@dataclass
class ChannelResult:
    success: bool
    error: str | None = None


class Channel(Protocol):
    name: str

    def send(self, message: ChannelMessage) -> ChannelResult: ...
