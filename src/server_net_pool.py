# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import settings
from net_pool import NetPool
from settings import logger


class ServerNetPool(NetPool):
    def find_neighbour(self, connection):
        self.clean_connections_list()
        self.init_peer_pool_attributes(connection)
        for neighbour_connection in self.connections_list:
            if neighbour_connection is connection:
                continue
            if connection in neighbour_connection.peer_connections:
                continue
            self.update_peer_pool_attributes(connection, neighbour_connection)
            return neighbour_connection
        return None

    def init_peer_pool_attributes(self, connection):
        if not hasattr(connection, 'peer_connections'):
            connection.peer_connections = []

    def update_peer_pool_attributes(self, connection1, connection2):
        connection1.peer_connections.append(connection2)
        connection2.peer_connections.append(connection1)

    def can_be_disconnected(self, connection):
        return len(connection.peer_connections) >= settings.peer_connections
