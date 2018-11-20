import asyncio
import logging
import json
import aiohttp
from .stats import Stats

log = logging.getLogger(__name__)


class WebSocket:
    def __init__(self, node, host: str, port: int, password: str):
        self._node = node
        self._lavalink = self._node._manager._lavalink

        self._session = self._lavalink._session
        self._ws = None
        self._message_queue = []
        self._shutdown = False

        self._host = host
        self._port = port
        self._password = password

        self._shards = self._lavalink._shard_count
        self._user_id = self._lavalink._user_id

        self._loop = self._lavalink._loop
        self._loop.create_task(self.connect())  # TODO: Consider making add_node an async function to prevent creating a bunch of tasks?

    @property
    def connected(self):
        """ Returns whether the websocket is connected to Lavalink. """
        return bool(self._ws) and not self._ws.closed

    async def connect(self):
        """ Attempts to establish a connection to Lavalink. """
        headers = {
            'Authorization': self._password,
            'Num-Shards': self._shards,
            'User-Id': str(self._user_id)
        }

        try:
            self._ws = await self._session.ws_connect('ws://{}:{}'.format(self._host, self._port), headers=headers)
        except aiohttp.ClientConnectorError:
            log.warning('Failed to connect to node `{}`, retrying in 5s...'.format(self._node.name))
            await asyncio.sleep(5.0)
            await self.connect()  # TODO: Consider a backoff or max retry attempt. max_attempts seems redundant as a connection is needed
        else:
            asyncio.ensure_future(self._listen())

    async def _listen(self):
        while self.connected:
            msg = await self._ws.receive()
            log.debug('Received websocket message from node `{}`: {}'.format(self._node.name, msg.data))

            if msg.type == aiohttp.WSMsgType.text:
                await self._handle_message(json.loads(msg.data))
            elif msg.type == aiohttp.WSMsgType.close or \
                    msg.type == aiohttp.WSMsgType.closing or \
                    msg.type == aiohttp.WSMsgType.closed:
                await self._ws_disconnect(msg.data, msg.extra)
                return

    async def _handle_message(self, data: dict):
        op = data['op']

        if op == 'stats':
            self._node.stats = Stats(self._node, data)

    async def _ws_disconnect(self, code: int, reason: str):
        log.warning('Disconnected from node `{}` ({}): {}'.format(self._node.name, code, reason))
        self._ws = None

        if not self._shutdown:
            await self.connect()

    async def _send(self, **data):
        if self.connected:
            log.debug('Sending payload {}'.format(str(data)))
            await self._ws.send_json(data)
        else:
            log.debug('Send called node `{}` ready, payload queued: {}'.format(self._node.name, str(data)))
            self._message_queue.append(data)
