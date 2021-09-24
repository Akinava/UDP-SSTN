# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from handler import Handler
from datagram import Datagram
from settings import logger


class ServerHandler(Handler):
    def hpn_neighbours(self, request):
        #logger.info('')
        self.__set_pub_key_to_connection(request)
        self.__set_encrypt_marker_to_connection(request)
        self.net_pool.find_neighbours(request.connection)

        if request.connection.peer_connections:
            logger.info('found neighbours {} for peer {}'.format(request.connection.peer_connections, request.connection))
            self.__processing_neighbors(request)
        else:
            logger.info('no neighbours for peer {}'.format(request.connection))
            self.hpn_ping(request.connection)

    def __processing_neighbors(self, request):
        self.__send_neighbours_response(request, request.connection, request.connection.peer_connections)
        for neighbour_connection in request.connection.peer_connections:
            self.__send_neighbours_response(request, neighbour_connection, [request.connection])
            self.__handle_disconnect(neighbour_connection)
        self.__handle_disconnect(request.connection)

    def __send_neighbours_response(self, request, receiving_connection, neighbours_connections):
        response = Datagram(receiving_connection)
        self.send(request=request,
                  response=response,
                  neighbours_connections=neighbours_connections)

    def get_hpn_clients_list(self, **kwargs):
        hpn_clients_list = []
        neighbours_connections = kwargs['neighbours_connections']
        for neighbour_connection in neighbours_connections:
            hpn_clients_list.append(self.pack_neighbour_connection(neighbour_connection))
        return hpn_clients_list

    def pack_neighbour_connection(self, neighbour_connection):
        client_data_structure = self.parser().protocol.lists.hpn_clients_list.structure
        return self.make_message_by_structure(
            structure=client_data_structure,
            client_data=neighbour_connection)

    def get_hpn_clients_pub_key(self, **kwargs):
        return kwargs['client_data'].get_pub_key()

    def get_hpn_clients_addr(self, **kwargs):
        return kwargs['client_data'].get_remote_addr()

    def get_disconnect_flag(self, **kwargs):
        return self.net_pool.can_be_disconnected(kwargs['response'].connection)

    def __set_pub_key_to_connection(self, request):
        connection_pub_key = request.unpack_message.requester_pub_key
        request.connection.set_pub_key(connection_pub_key)

    def __set_encrypt_marker_to_connection(self, request):
        encrypt_marker = request.unpack_message.encrypted_request_marker
        request.connection.set_encrypt_marker(encrypt_marker)

    def __handle_disconnect(self, connection):
        if self.net_pool.can_be_disconnected(connection):
            self.net_pool.disconnect(connection)
