# flake8: noqa

__title__ = 'Lavalink'
__author__ = 'Devoxin'
__license__ = 'MIT'
__copyright__ = 'Copyright 2019 Devoxin'
__version__ = '3.0.0'


import logging
import inspect
import sys

from .events import Event, TrackStartEvent, TrackStuckEvent, TrackExceptionEvent, TrackEndEvent, QueueEndEvent, \
    NodeConnectedEvent, NodeChangedEvent, NodeDisconnectedEvent, WebSocketClosedEvent
from .models import BasePlayer, DefaultPlayer, AudioTrack, NoPreviousTrack, InvalidTrack
from .utils import format_time, parse_time
from .client import Client, _event_hooks
from .playermanager import PlayerManager
from .exceptions import NodeException
from .nodemanager import NodeManager
from .stats import Penalty, Stats
from .websocket import WebSocket
from .node import Node


def enable_debug_logging():
    """
    Sets up a logger to stdout. This solely exists to make things easier for
    end-users who want to debug issues with Lavalink.py.
    """
    log = logging.getLogger('lavalink')

    fmt = logging.Formatter(
        '[%(asctime)s] [lavalink.py] [%(levelname)s] %(message)s',
        datefmt="%H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    log.addHandler(handler)

    log.setLevel(logging.DEBUG)


def add_event_hook(*hooks, event: Event = None):
    """
    Adds an event hook to be dispatched on an event.

    Parameters
    ----------
    hooks: function
        The hooks to register for the given event type.
        If `event` parameter is left empty, then it will run when any event is dispatched.
    event: Event
        The event the hook belongs to. This will dispatch when that specific event is
        dispatched.
    """
    if event is not None and not isinstance(event, Event):
        raise TypeError('Event parameter is not of type Event or None')

    event_hooks = _event_hooks.get(event, [])

    for hook in hooks:
        if not callable(hook) or not inspect.iscoroutinefunction(hook):
            raise TypeError('Hook is not callable or a coroutine')

        if hook not in event_hooks:
            if not event_hooks:
                _event_hooks[event or 'Generic'] = [hook]
            else:
                _event_hooks[event or 'Generic'].append(hook)


def on(event: Event = None):
    """
    Adds an event hook when decorated with a function.

    Parameters
    ----------
    event: Event
        The event that will dispatch the given event hook. This defaults
        to 'Generic', which is dispatched on all events.
    """
    def decorator(func):
        add_event_hook(func, event)

    return decorator
