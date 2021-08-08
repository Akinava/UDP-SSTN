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
    def hpn_neighbour_client(self):
        logger.info('')
        self.__set_pub_key_to_connection()
        self.__set_encrypt_marker_to_connection()
        self.neighbour_connection = self.net_pool.find_neighbour(self.connection)
        if self.neighbour_connection:
            logger.info('found neighbour {} for peer {}'.format(self.neighbour_connection, self.connection))
            self.__send_hpn_neighbour_client_response()
            self.__handle_disconnect()
        else:
            logger.info('no neighbours for peer {}'.format(self.connection))
        self.__update_connections_state()

    def __send_hpn_neighbour_client_response(self):
        receiver_message = self.__make_connection_message(self.connection, self.neighbour_connection)
        neighbour_message = self.__make_connection_message(self.neighbour_connection, self.connection)
        self.send(message=receiver_message,
                  connection=self.connection,
                  package_protocol_name='hpn_neighbour_client')
        self.send(message=neighbour_message,
                  connection=self.neighbour_connection,
                  package_protocol_name='hpn_neighbour_client')

    def __make_connection_message(self, receiver_connection, neighbour_connection):
        return self.make_message(
            package_name='hpn_neighbour_client',
            receiver_connection=receiver_connection,
            neighbour_connection=neighbour_connection)

    def get_neighbour_pub_key(self, **kwargs):
        return kwargs['neighbour_connection'].get_pub_key()

    def get_neighbour_addr(self, **kwargs):
        return self.parser.pack_addr(kwargs['neighbour_connection'].get_remote_addr())

    def get_disconnect_flag(self, **kwargs):
        return self.parser.pack_bool(self.net_pool.can_be_disconnected(kwargs['receiver_connection']))

    def __set_pub_key_to_connection(self):
        connection_pub_key = self.parser.get_part('requester_pub_key')
        self.connection.set_pub_key(connection_pub_key)

    def __set_encrypt_marker_to_connection(self):
        encrypt_marker = self.parser.get_part('encrypted_request_marker')
        self.connection.set_encrypt_marker(encrypt_marker)

    def __update_connections_state(self):
        stat = 'waiting' if self.neighbour_connection is None else 'in_progress'
        self.__save_neighbour_connection_param(stat)

    def __handle_disconnect(self, *connections):
        for connection in connections:
            if self.net_pool.can_be_disconnected(connection):
                self.net_pool.disconnect(connection)

    def __save_neighbour_connection_param(self, state):
        self.net_pool.update_neighbour_group(self.connection, self.neighbour_connection)
        self.net_pool.update_state(self.connection, state)
        self.net_pool.update_state(self.neighbour_connection, state)
