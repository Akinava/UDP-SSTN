# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import signal
import settings
from settings import logger
from connection import Connection, NetPool
import utilit


class UDPHost:
    def __init__(self, handler):
        logger.debug('')
        self.handler = handler
        self.net_pool = NetPool()
        self.listener = None
        self.local_host = settings.local_host
        self.set_posix_handler()

    def set_posix_handler(self):
        signal.signal(signal.SIGUSR1, self.handle_posix_signal)
        signal.signal(signal.SIGTERM, self.handle_posix_signal)

    def handle_posix_signal(self, signum, frame):
        if signum == signal.SIGTERM:
            self.exit()
        if signum == signal.SIGUSR1:
            self.config_reload()

    async def create_listener(self, port):
        loop = asyncio.get_running_loop()
        logger.info('host create_listener on port {}'.format(port))

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.handler(),
            local_addr=(self.local_host, port))
        self.listener = Connection()
        self.listener.set_listener(
            local_port=port,
            transport=transport,
            protocol=protocol)

    async def serve_forever(self):
        logger.debug('')
        while self.listener.is_alive():
            self.ping_connections()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def ping_connections(self):
        for connection in self.net_pool.get_all_connections():
            connection.send(self.handler.do_swarm_ping())

    def shutdown_connections(self):
        self.net_pool.clean()

    def config_reload(self):
        logger.debug('')
        utilit.import_config()

    def exit(self):
        logger.info('')
        self.listener.shutdown()
        self.shutdown_connections()

    def __del__(self):
        logger.debug('')
