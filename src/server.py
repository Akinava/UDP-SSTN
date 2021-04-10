#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import asyncio
import settings
from settings import logger
import host
import protocol
from utilit import pack_host, pack_port, binary_not


class ServerHandler(protocol.GeneralProtocol):
    disconnect_flag = b'\xff'
    keep_connection_flag = b'\x00'

    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_request': 'swarm_peer_response',
    }

    def do_swarm_peer_response(self, connection):
        logger.info('')
        self.set_connection_fingerprint(connection)
        self.save_client_in_group_list(connection)
        neighbour_connection = self.find_neighbour(connection)
        if neighbour_connection:
            self.send_swarm_response(connection, neighbour_connection)
            self.handle_disconnect([connection, neighbour_connection])
        self.update_connections_state(connection, neighbour_connection)

    def update_connections_state(self, connection, neighbour_connection):
        stat = 'wait' if neighbour_connection is None else 'in_progress'
        self.save_connection_param(connection, stat, neighbour_connection)
        self.save_connection_param(neighbour_connection, stat, connection)

    def handle_disconnect(self, connections):
        for connection in connections:
            if self.get_disconnect_flag(connection) != self.disconnect_flag:
                continue
            self.disconnect(connection)

    def disconnect(self, connection):
        group = self.get_connection_group(connection)
        del group[connection]
        connection.shutdown()

    def set_connection_fingerprint(self, connection):
        fingerprint_beginning = self.crypt_tools.get_fingerprint_len()
        fingerprint_end = self.crypt_tools.get_fingerprint_len() * 2
        connection.set_fingerprint(connection.get_request()[fingerprint_beginning: fingerprint_end])

    def save_client_in_group_list(self, connection):
        if connection in self.connections_group_0 or connection in self.connections_group_1:
            return
        if len(self.connections_group_0) > len(self.connections_group_1):
            self.connections_group_1[connection] = {}
            return
        self.connections_group_0[connection] = {}

    def send_swarm_response(self, connection, neighbour_connection):
        sign_message = self.make_connection_message(connection, neighbour_connection)
        neighbour_sign_message = self.make_connection_message(neighbour_connection, connection)
        connection.send(sign_message)
        neighbour_connection.send(neighbour_sign_message)
        return neighbour_connection

    def get_disconnect_flag(self, connection):
        param = self.get_connection_param(connection)
        connection_groups = param.get('groups', set())
        group = self.get_connection_group(connection)
        return self.disconnect_flag if len(group) > settings.peer_connections and len(connection_groups) == 2 else self.keep_connection_flag

    def get_connection_group(self, connection):
        if connection in self.connections_group_0:
            return self.connections_group_0
        if connection in self.connections_group_1:
            return self.connections_group_1
        return None

    def make_connection_message(self, connection0, connection1):
        disconnect_flag = self.get_disconnect_flag(connection0)
        message = connection0.get_fingerprint() + connection1.get_request() + connection1.dump_addr() + disconnect_flag
        return self.sign_message(message)

    def get_connection_param(self, connection):
        return self.connections_group_0.get(connection) or self.connections_group_1.get(connection)

    def save_connection_param(self, connection, state, neighbour_connection=None):
        if connection in None:
            return
        param = self.get_connection_param(connection)
        param['state'] = state
        if neighbour_connection is None:
            return
        group = 0 if neighbour_connection in self.connections_group_0 else 1
        connection_groups = param.get('groups', set())
        connection_groups.add(group)
        param['groups'] = connection_groups

    def find_neighbour(self, connection):
        param = self.get_connection_param(connection)
        connection_groups_index = param.get('groups', set())
        if len(connection_groups_index) != 1:
            connections_group = self.get_any_group()
        else:
            connections_group = self.get_group_by_index(binary_not(next(iter(connection_groups_index))))
        neighbour_connection= self.find_waiting_connection(connections_group)
        return neighbour_connection

    def get_group_by_index(self, index):
        return getattr(self, 'connections_group_{}'.format(index))

    def get_any_group(self):
        connections_group = {}
        connections_group.update(self.connections_group_0)
        connections_group.update(self.connections_group_1)
        return connections_group

    def find_waiting_connection(self, group):
        for connection, params in group.items():
            if params.get('state') == 'waiting':
                return connection
        return None

    def sign_message(self, message):
        return self.crypt_tools.sign_message(message)


class Server(host.UDPHost):
    async def run(self):
        logger.info('')
        await self.create_listener(settings.default_port)
        await self.serve_forever()


if __name__ == '__main__':
    logger.info('server start')
    server = Server(handler=ServerHandler)
    asyncio.run(server.run())
    logger.info('server shutdown')
