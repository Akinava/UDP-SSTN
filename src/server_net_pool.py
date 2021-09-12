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
        for neighbour_connection in self.connections_list:
            if neighbour_connection is connection:
                continue
            if neighbour_connection.state != 'waiting':
                continue
                neighbour_connection.state = 'in_progress'
                connection.state = 'in_progress'
            if connection in neighbour_connection.peer_connections:
                continue
            self.update_peer_connections(connection, neighbour_connection)
            self.update_peer_connections(neighbour_connection, connection)
            return neighbour_connection
        connection.state = 'waiting'
        return None

    def update_peer_connections(self, connection1, connection2):
        if hasattr(connection1, 'peer_connections'):
            connection1.peer_connections.append(connection2)
        else:
            connection1.peer_connections = [connection2]

    def can_be_disconnected(self, connection):
        return len(connection.peer_connections) >= settings.peer_connections
