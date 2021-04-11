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
from utilit import unpack_stream


class ServerHandler(protocol.GeneralProtocol):
    disconnect_flag = b'\xff'
    keep_connection_flag = b'\x00'

    protocol = {
        'request': 'response',
        'swarm_ping': None,
        'swarm_peer_request': 'swarm_peer_response',
    }

    def define_swarm_peer_request(self, connection):
        check_request_len = self.crypt_tools.get_fingerprint_len() * 2 == len(connection.get_request())
        my_fingerprint = self.parse_swarm_peer_request(connection)['my_fingerprint']
        check_fingerprint = my_fingerprint == self.crypt_tools.get_fingerprint()
        return check_request_len and check_fingerprint

    def parse_swarm_peer_request(self, connection):
        request = connection.get_request()
        my_fingerprint, client_fingerprint = binary_not(request, self.crypt_tools.get_fingerprint_len())
        return {'my_fingerprint': my_fingerprint, 'client_fingerprint': client_fingerprint}

    def do_swarm_peer_response(self, connection):
        logger.info('')
        self.set_fingerprint_to_connection_from_swarm_peer_request(connection)
        self.net_pool.save_connection(connection)
        neighbour_connection = self.net_pool.find_neighbour(connection)
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

    def set_fingerprint_to_connection_from_swarm_peer_request(self, connection):
        client_fingerprint = self.parse_swarm_peer_request(connection)['client_fingerprint']
        connection.set_fingerprint(client_fingerprint)

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
