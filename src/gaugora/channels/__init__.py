"""Notification channels (Strategy)."""

from gaugora.channels.base import Channel, ChannelMessage, ChannelResult
from gaugora.channels.email import EmailChannel

__all__ = ["Channel", "ChannelMessage", "ChannelResult", "EmailChannel"]
