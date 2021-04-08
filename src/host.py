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
from connection import Connection
import utilit


class UDPHost:
    def __init__(self, handler):
        logger.info('')
        self.handler = handler
        self.connections = []
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

    def connect(self, host, port):
        logger.info('host connect to {} {}'.format(host, port))

    async def create_listener(self, port):
        logger.info('')
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

    async def send(self, connection, message, local_port=None):
        logger.info('')

        loop = asyncio.get_running_loop()
        on_con_lost = loop.create_future()
        local_addr = (self.local_host, local_port) if local_port else None

        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.handler(message, on_con_lost),
            remote_addr=connection.get_remote_addr(),
            local_addr=local_addr)

        connection.set_transport(transport)
        connection.set_protocol(protocol)
        connettion.set_net(self.connections)
        self.connections.append(connection)

        try:
            await on_con_lost
        finally:
            connection.close_transport()

    async def serve_forever(self):
        logger.info('')
        while self.listener.is_alive():
            self.ping_connections()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def ping_connections(self):
        for connection in self.connections:
            if not connection.is_time_out():
                self.send(connection, self.handler.do_swarm_ping())
            else:
                connection.shutdown()

    def shutdown_connections(self):
        for connection in self.connections:
            connection.shutdown()

    def config_reload(self):
        logger.info('')
        utilit.import_config()

    def exit(self):
        logger.info('')
        self.listener.close_transport()
        self.shutdown_connections()

    def __del__(self):
        logger.info('')
