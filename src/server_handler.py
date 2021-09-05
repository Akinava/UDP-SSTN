# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]

from time import time
from handler import Handler
import settings
from settings import logger


class ServerHandler(Handler):
    def hpn_neighbour_client(self, connection):
        #logger.info('')
        self.__set_pub_key_to_connection(connection)
        self.__set_encrypt_marker_to_connection(connection)
        neighbour_connection = self.net_pool.find_neighbour(connection)
        if neighbour_connection:
            logger.info('found neighbour {} for peer {}'.format(neighbour_connection, connection))
            self.__send_hpn_neighbour_client_response(connection, neighbour_connection)
            self.__handle_disconnect(neighbour_connection, connection)
        else:
            logger.info('no neighbours for peer {}'.format(connection))
        self.__update_connections_state(connection, neighbour_connection)

    def __send_hpn_neighbour_client_response(self, connection1, connection2):
        connection1_message = self.__make_connection_message(connection1, connection2)
        connection2_message = self.__make_connection_message(connection2, connection1)

        self.send(message=connection1_message,
                  receiving_connection=connection1,
                  package_protocol_name='hpn_neighbour_client')
        self.send(message=connection2_message,
                  receiving_connection=connection2,
                  package_protocol_name='hpn_neighbour_client')

    def __make_connection_message(self, receiving_connection, neighbour_connection):
        return self.make_message(
            package_protocol_name='hpn_neighbour_client',
            receiving_connection=receiving_connection,
            neighbour_connection=neighbour_connection)

    def get_neighbour_pub_key(self, **kwargs):
        return kwargs['neighbour_connection'].get_pub_key()

    def get_neighbour_addr(self, **kwargs):
        return self.parser().pack_addr(kwargs['neighbour_connection'].get_remote_addr())

    def get_disconnect_flag(self, **kwargs):
        disconnect_flag = self.net_pool.can_be_disconnected(kwargs['receiving_connection'])
        return self.parser().pack_bool(disconnect_flag)

    def __set_pub_key_to_connection(self, connection):
        connection_pub_key = connection.get_unpack_request_part('requester_pub_key')
        connection.set_pub_key(connection_pub_key)

    def __set_encrypt_marker_to_connection(self, connection):
        encrypt_marker = connection.get_unpack_request_part('encrypted_request_marker')
        connection.set_encrypt_marker(encrypt_marker)

    def __update_connections_state(self, connection, neighbour_connection):
        stat = 'waiting' if neighbour_connection is None else 'in_progress'
        self.__save_neighbour_connection_param(stat, connection, neighbour_connection)

    def __handle_disconnect(self, *connections):
        for connection in connections:
            if self.net_pool.can_be_disconnected(connection):
                self.net_pool.disconnect(connection)

    def __save_neighbour_connection_param(self, state, connection, neighbour_connection):
        self.net_pool.update_neighbour_group(connection, neighbour_connection)
        self.net_pool.update_state(connection, state)
        self.net_pool.update_state(neighbour_connection, state)
