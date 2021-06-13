# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from time import time
from parser import Parser
from handler import Handler


class ServerHandler(Handler):
    def verify_len_swarm_peer_request(self, **kwarg):
        request_length = len(self.connection.get_request())
        required_length = self.parser.calc_requared_length()
        return required_length == request_length

    def verify_package_id_marker(self, **kwarg):
        package_protocol = kwarg['package_protocol']
        request_id_marker = self.parser.get_part('package_id_marker')
        required_id_marker = package_protocol['package_id_marker']
        return request_id_marker == required_id_marker

    def verify_timestamp(self, **kwarg):
        timestamp = self.parser.get_part('timestamp')
        return time() - settings.peer_ping_time_seconds < timestamp < time() + settings.peer_ping_time_seconds

    def verify_package_id_marker(self, **kwarg):
        my_fingerprint_from_request = self.parser.get_part('my_fingerprint')
        my_fingerprint_reference = self.crypt_tools.get_fingerprint()
        return my_fingerprint_from_request == my_fingerprint_reference

    def swarm_peer(self):
        logger.info('')
        self.__set_open_key_to_connection()
        self.__set_encrypt_marker_to_connection()
        self.neighbour_connection = self.net_pool.find_neighbour(self.connection)
        if self.neighbour_connection:
            self.__send_swarm_response()
            self.__handle_disconnect()
        self.__update_connections_state()

    def __send_swarm_response(self):
        receiver_message = self.__make_connection_message(self.connection, self.connection_neighbour)
        neighbour_message = self.__make_connection_message(self.connection_neighbour, self.connection)
        self.connection.send(self.__handle_encrypt_marker(receiver_message, self.connection))
        self.connection_neighbour.send(self.__handle_encrypt_marker(neighbour_message, self.connection_neighbou))

    def __make_connection_message(self, connection_receiver, connection_neighbour):
        return self.make_message(
            package_name='swarm_peer',
            connection_receiver=connection_receiver,
            connection_neighbour=connection_neighbour)

    def get_package_id_marker(self, **kwarg):
        marker = self.parser.find_protocol_package(kwargs['package_name'])['package_id_marker']
        return self.parser.pack_int(marker, 1)

    def get_neighbour_open_key(self, **kwarg):
        return kwarg['connection_neighbour'].get_open_key()

    def get_neighbour_addr(self, **kwarg):
        return self.parser.pack_addr(kwarg['connection_neighbour'].get_remote_addr())

    def get_disconnect_flag(self, **kwarg):
        return self.parser.pack_bool(self.net_pool.can_be_disconnected(kwarg['connection_receiver']))

    def get_timestamp(self, **kwarg):
        return self.parser.pack_timestemp()

    def get_receiver_fingerprint(self, **kwarg):
        return kwarg['connection_receiver'].get_fingerprint()

    def __set_open_key_to_connection(self):
        connection_open_key = self.parser.get_part('requester_open_key')
        self.connection.set_open_key(connection_open_key)

    def __set_encrypt_marker_to_connection(self):
        encrypt_marker = self.parser.get_part('encrypted_request_marker')
        self.connection.set_encrypt_marker(encrypt_marker)

    def __update_connections_state(self):
        stat = 'wait' if self.neighbour_connection is None else 'in_progress'
        self.__save_neighbour_connection_param(stat)

    def __handle_disconnect(self, *connections):
        for connection in connections:
            if self.net_pool.can_be_disconnected(connection):
                self.net_pool.disconnect(connection)

    def __save_neighbour_connection_param(self, state):
        self.net_pool.update_neighbour_group(self.connection, self.neighbour_connection)
        self.net_pool.update_state(self.connection, state)
        self.net_pool.update_state(self.neighbour_connection, state)

    def __sign_message(self, message):
        return self.crypt_tools.sign_message(message)

    def __encrypt_message(self, message, connection):
        return self.crypt_tools.sign_message(message, connection.get_open_key())

    def __handle_encrypt_marker(self, message, connection):
        if connection.get_encrypt_marker():
            return self.__encrypt_message(message, connection)
        return self.__sign_message(message)
