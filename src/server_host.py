#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
from settings import logger
from host import Host
from server_handler import ServerHandler
from protocol import PROTOCOL
from server_net_pool import ServerNetPool


if __name__ == '__main__':
    logger.info('server start')
    server = Host(net_pool=ServerNetPool, handler=ServerHandler, protocol=PROTOCOL)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info('server interrupted')
    logger.info('server shutdown')
