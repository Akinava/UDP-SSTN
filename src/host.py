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


class Host:
    def __init__(self, handler):
        logger.debug('')
        self.__handler = handler
        self.__net_pool = NetPool()
        self.__local_host = settings.local_host
        self.__set_posix_handler()

    def __set_posix_handler(self):
        signal.signal(signal.SIGUSR1, self.__handle_posix_signal)
        signal.signal(signal.SIGTERM, self.__handle_posix_signal)

    def __handle_posix_signal(self, signum, frame):
        if signum == signal.SIGTERM:
            self.__exit()
        if signum == signal.SIGUSR1:
            self.__config_reload()

    async def create_endpoint(self, local_host, local_port):
        logger.info('create listener on port {}'.format(local_port))
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: self.__handler(),
            local_addr=(local_host, local_port))
        connection = Connection(
            local_host=local_host,
            local_port=local_port,
            transport=transport
        )
        return connection

    async def serve_forever(self):
        logger.debug('')
        while self.listener.is_alive():
            self.__ping_connections()
            await asyncio.sleep(settings.peer_ping_time_seconds)

    def __ping_connections(self):
        for connection in self.__net_pool.get_all_connections():
            if connection.last_response_is_over_ping_time():
                self.__handler.do_swarm_ping(connection)

    def __shutdown_connections(self):
        self.__net_pool.shutdown()

    def __config_reload(self):
        logger.debug('')
        utilit.import_config()

    def __exit(self):
        logger.info('')
        self.__listener.shutdown()
        self.__shutdown_connections()

    def __del__(self):
        logger.debug('')
