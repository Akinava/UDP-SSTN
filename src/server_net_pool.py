# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import settings
from net_pool import NetPool


class ServerNetPool(NetPool):
    def find_neighbours(self, connection):
        self.clean_connections_list()
        self.init_peer_pool_attributes(connection)
        for neighbour_connection in self.connections_list:
            if neighbour_connection is connection:
                continue
            if connection in neighbour_connection.peer_connections:
                continue
            self.update_peer_pool_attributes(connection, neighbour_connection)
            if self.has_enough_connections(connection):
                return
        return

    def init_peer_pool_attributes(self, connection):
        if not hasattr(connection, 'peer_connections'):
            connection.peer_connections = []

    def update_peer_pool_attributes(self, connection1, connection2):
        connection1.peer_connections.append(connection2)
        connection2.peer_connections.append(connection1)

    def has_enough_connections(self, connection):
        return len(connection.peer_connections) >= settings.peer_connections

    def get_pending_connections(self):
        pending_connections = []
        for connection in self.connections_list:
            if not self.has_enough_connections(connection):
                pending_connections.append(connection)
        return pending_connections

    def get_tail_connections(self):
        return self.connections_list[-settings.peer_connections: ]

    def can_be_disconnected(self, connection):
        if not self.has_enough_connections(connection):
            return False
        if connection in self.get_pending_connections():
            return False
        if connection in self.get_tail_connections():
            return False
        return True
