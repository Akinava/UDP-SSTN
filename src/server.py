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
import handler
from utilit import unpack_stream


class ServerHandler(handler.Protocol):
    disconnect_flag = b'\xff'
    keep_connection_flag = b'\x00'

    protocol = {
        '__request': 'response',
        'swarm_ping': None,
        'swarm_peer_request': 'swarm_peer_response',
    }

    def define_swarm_peer_request(self, connection):
        if self.__verify_len_swarm_peer_request(connection) is False:
            return False
        if self.__verify_my_fingerprint_in_swarm_peer_request(connection) is False:
            return False
        return True

    def __verify_len_swarm_peer_request(self, connection):
        fingerprint_len = self.crypt_tools.get_fingerprint_len()
        port_info_len = 4
        return fingerprint_len * 2 == len(connection.get_request())

    def __verify_my_fingerprint_in_swarm_peer_request(self, connection):
        my_fingerprint = self.__parse_swarm_peer_request(connection)['my_fingerprint']
        return my_fingerprint == self.crypt_tools.get_fingerprint()

    def __parse_swarm_peer_request(self, connection):
        request = connection.get_request()
        my_fingerprint, client_fingerprint = unpack_stream(request, self.crypt_tools.get_fingerprint_len())
        return {'my_fingerprint': my_fingerprint,
                'client_fingerprint': client_fingerprint}

    def do_swarm_peer_response(self, connection):
        logger.info('')
        self.__set_fingerprint_to_connection_from_swarm_peer_request(connection)
        neighbour_connection = self.net_pool.find_neighbour(connection)
        if neighbour_connection:
            self.__send_swarm_response(connection, neighbour_connection)
            self.__handle_disconnect(connection, neighbour_connection)
        self.__update_connections_state(connection, neighbour_connection)

    def __update_connections_state(self, connection, neighbour_connection):
        stat = 'wait' if neighbour_connection is None else 'in_progress'
        self.__save_connection_param(connection, neighbour_connection, stat)

    def __handle_disconnect(self, *connections):
        for connection in connections:
            if self.net_pool.can_be_disconnected(connection):
                self.net_pool.disconnect(connection)

    def __set_fingerprint_to_connection_from_swarm_peer_request(self, connection):
        client_fingerprint = self.__parse_swarm_peer_request(connection)['client_fingerprint']
        connection.set_fingerprint(client_fingerprint)

    def __send_swarm_response(self, connection, neighbour_connection):
        sign_message = self.__make_connection_message(connection, neighbour_connection)
        neighbour_sign_message = self.__make_connection_message(neighbour_connection, connection)
        connection.send(sign_message)
        neighbour_connection.send(neighbour_sign_message)

    def __get_disconnect_flag(self, connection):
        if self.net_pool.can_be_disconnected(connection):
            return self.disconnect_flag
        return self.keep_connection_flag

    def __make_connection_message(self, connection0, connection1):
        disconnect_flag = self.__get_disconnect_flag(connection0)
        message = connection0.get_fingerprint() + \
                  connection1.get_fingerprint() + \
                  connection1.dump_addr() + \
                  disconnect_flag
        return message + self.__sign_message(message)

    def __save_connection_param(self, connection, neighbour_connection, state):
        self.net_pool.update_neighbour_group(connection, neighbour_connection)
        self.net_pool.update_state(connection, state)
        self.net_pool.update_state(neighbour_connection, state)

    def __sign_message(self, message):
        return self.crypt_tools.sign_message(message)


class Server(host.Host):
    async def run(self):
        logger.info('')
        self.listener = await self.create_endpoint(settings.local_host, settings.default_port)
        await self.serve_forever()


if __name__ == '__main__':
    logger.info('server start')
    server = Server(handler=ServerHandler)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info('server interrupted')
    logger.info('server shutdown')
