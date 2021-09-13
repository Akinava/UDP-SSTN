# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
import settings
from datagram import Datagram
from settings import logger


class ServerHandler(Handler):
    def hpn_neighbour_client(self, request):
        #logger.info('')
        self.__set_pub_key_to_connection(request)
        self.__set_encrypt_marker_to_connection(request)
        neighbour_connection = self.net_pool.find_neighbour(request.connection)
        if neighbour_connection:
            logger.info('found neighbour {} for peer {}'.format(neighbour_connection, request.connection))
            self.__send_hpn_neighbour_client_response(request, request.connection, neighbour_connection)
            self.__send_hpn_neighbour_client_response(request, neighbour_connection, request.connection)
            self.__handle_disconnect(request.connection)
            self.__handle_disconnect(neighbour_connection)
        else:
            logger.info('no neighbours for peer {}'.format(request.connection))

    def __send_hpn_neighbour_client_response(self, request, receiving_connection, neighbour_connection):
        response = Datagram(receiving_connection)
        self.send(request=request,
                  response=response,
                  neighbour_connection=neighbour_connection)

    def get_neighbour_pub_key(self, **kwargs):
        return kwargs['neighbour_connection'].get_pub_key()

    def get_neighbour_addr(self, **kwargs):
        return self.parser().pack_addr(kwargs['neighbour_connection'].get_remote_addr())

    def get_disconnect_flag(self, **kwargs):
        disconnect_flag = self.net_pool.can_be_disconnected(kwargs['neighbour_connection'])
        return self.parser().pack_bool(disconnect_flag)

    def __set_pub_key_to_connection(self, request):
        connection_pub_key = request.unpack_message.requester_pub_key
        request.connection.set_pub_key(connection_pub_key)

    def __set_encrypt_marker_to_connection(self, request):
        encrypt_marker = request.unpack_message.encrypted_request_marker
        request.connection.set_encrypt_marker(encrypt_marker)

    def __handle_disconnect(self, *connections):
        for connection in connections:
            if self.net_pool.can_be_disconnected(connection):
                self.net_pool.disconnect(connection)

    def __save_neighbour_connection_param(self, state, connection, neighbour_connection):
        self.net_pool.update_neighbour_group(connection, neighbour_connection)
        self.net_pool.update_state(connection, state)
        self.net_pool.update_state(neighbour_connection, state)
