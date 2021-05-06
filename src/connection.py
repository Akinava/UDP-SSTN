# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import struct
from time import time
from utilit import Singleton, next_element_of_ring
import settings
from settings import logger


class Connection:
    def __init__(self):
        self.__set_last_response()
        self.__set_last_request()

    def __eq__(self, connection):
        if self.__remote_host != connection.__remote_host:
            return False
        if self.__remote_port != connection.__remote_port:
            return False
        return True

    def is_alive(self):
        if self.transport.is_closing():
            return False
        return True

    def last_request_is_time_out(self):
        return time() - self.__last_request > settings.peer_timeout_seconds

    def last_response_is_over_ping_time(self):
        return time() - self.__last_response > settings.peer_ping_time_seconds

    def __set_last_response(self):
        self.__last_response = time()

    def __set_last_request(self):
        self.__last_request = time()

    def __set_transport(self, transport):
        self.transport = transport

    def __set_protocol(self, protocol):
        self.__protocol = protocol

    def __set_local_port(self, local_port):
        self.local_port = local_port

    def __set_remote_host(self, remote_host):
        self.__remote_host = remote_host

    def __set_remote_port(self, remote_port):
        self.__remote_port = remote_port

    def __set_request(self, request):
        self.__request = request

    def get_request(self):
        return self.__request

    def set_fingerprint(self, fingerprint):
        self.fingerprint = fingerprint

    def get_fingerprint(self):
        return self.fingerprint

    def dump_addr(self):
        return struct.pack('>BBBBH', *(map(int, self.__remote_host.split('.'))), self.__remote_port)

    def set_listener(self, local_port, transport, protocol):
        self.__set_protocol(protocol)
        self.__set_transport(transport)
        self.__set_local_port(local_port)

    def datagram_received(self, request, remote_addr, transport):
        self.set_remote_addr(remote_addr)
        self.__set_request(request)
        self.__set_transport(transport)

    def set_remote_addr(self, addr):
        self.__set_remote_host(addr[0])
        self.__set_remote_port(addr[1])

    def send(self, response):
        logger.info('')
        self.__set_last_response()
        self.transport.sendto(response, (self.__remote_host, self.__remote_port))

    def shutdown(self):
        if self.transport.is_closing():
            return
        self.transport.close()


class NetPool(Singleton):
    def __init__(self):
        self.__groups = [{}, {}]

    def __clean_groups(self):
        for group_index in range(len(self.__groups)):
            alive_group_tmp = {}
            for connection, param in self.__groups[group_index].items():
                if connection.last_request_is_time_out():
                    connection.shutdown()
                    continue
                alive_group_tmp[connection] = param
            self.__groups[group_index] = alive_group_tmp

    def __join_groups(self):
        result_group = {}
        for group in self.__groups:
            result_group.update(group)
        return result_group

    def __get_connection_param(self, connection):
        return self.__join_groups().get(connection)

    def __get_connection_group(self, connection):
        for group in self.__groups:
            if connection in group:
                return group
        return None

    def __find_waiting_connection(self, group):
        for connection, params in group.items():
            if params.get('state') == 'waiting':
                return connection
        return None

    def find_neighbour(self, connection):
        self.__clean_groups()
        param = self.__get_connection_param(connection)
        connection_groups_index = param.get('groups', set())
        if len(connection_groups_index) != 1:
            group = self.get_all_connections()
        else:
            current_group_index = next(iter(connection_groups_index))
            required_group_index = next_element_of_ring(current_group_index)
            group = self.__groups[required_group_index]
        neighbour_connection = self.__find_waiting_connection(group)
        return neighbour_connection

    def __get_group_by_index(self, index):
        return self.__groups[index]

    def save_connection(self, connection):
        if not self.self.__get_connection_group(connection) is None:
            self.__update_connection_in_group(connection)
            self.update_state(connection, 'waiting')
            return
        self.__put_connection_in_group(connection)

    def __put_connection_in_group(self, connection):
        state = {'state': 'waiting', 'groups': set()}
        if len(self.group_0) > len(self.group_1):
            self.group_1[connection] = state
        else:
            self.group_0[connection] = state

    def __update_connection_in_group(self, connection):
        group = self.__get_connection_group(connection)
        param = self.__get_connection_param(connection)
        group[connection] = param

    def get_all_connections(self):
        self.__clean_groups()
        group_all = self.__join_groups()
        return group_all

    def update_neighbour_group(self, connection0, connection1):
        if connection0 is None or connection1 is None:
            return
        connection0_group_index = self.self.__get_connection_group_index(connection0)
        connection1_group_index = self.self.__get_connection_group_index(connection1)
        param0 = self.__get_connection_param(connection0)
        param1 = self.__get_connection_param(connection1)
        param0['groups'].add(connection0_group_index)
        param1['groups'].add(connection1_group_index)

    def update_state(self, connection, state):
        param = self.__get_connection_param(connection)
        param['state'] = state

    def __get_connection_group_index(self, connection):
        if connection in self.group_0:
            return 0
        if connection in self.group_1:
            return 1

    def can_be_disconnected(self, connection):
        group = self.__get_connection_group(connection)
        param = self.__get_connection_param(connection)
        connection_groups = param.get('groups', set())
        group_has_enough_connections = len(group) > settings.peer_connections
        connection_connected_to_all_groups  = len(connection_groups) == len(self.group_0, self.group_1)
        return group_has_enough_connections and connection_connected_to_all_groups

    def disconnect(self, connection):
        group = self.__get_connection_group(connection)
        del group[connection]
        connection.shutdown()

    def shutdown(self):
        for connection, _ in self.__join_groups():
            connection.shutdown()
        self.group_0, self.group_1 = {}, {}
