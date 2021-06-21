# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from time import time
import itertools
from utilit import Singleton
import settings
from settings import logger
from crypt_tools import Tools as CryptTools


class Connection:
    def __init__(self, local_host=None, local_port=None, remote_host=None, remote_port=None, transport=None):
        if local_host:
            self.__set_local_host(local_host)
        if local_port:
            self.__set_local_port(local_port)
        if remote_host:
            self.__set_remote_host(remote_host)
        if remote_port:
            self.__set_remote_port(remote_port)
        if transport:
            self.__set_transport(transport)
        self.__set_last_response()
        self.__set_last_request()

    def __eq__(self, connection):
        if self.__remote_host != connection.__remote_host:
            return False
        if self.__remote_port != connection.__remote_port:
            return False
        return True

    def __str__(self):
        return '{}:{}'.format(self.__remote_host, self.__remote_port)

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

    def __set_local_host(self, local_host):
        self.__local_host = local_host

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

    def update_request(self, connection):
        self.__request = connection.get_request()

    def set_open_key(self, open_key):
        self.open_key = open_key

    def get_open_key(self):
        return self.open_key

    def get_fingerprint(self):
        return CryptTools().make_fingerprint(self.open_key)

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

    def get_remote_addr(self):
        return (self.__remote_host, self.__remote_port)

    def set_encrypt_marker(self, encrypt_marker):
        self.__encrypt_marker = encrypt_marker

    def get_encrypt_marker(self):
        return self.__encrypt_marker

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
        self.__groups = []
        self.__init_groups()

    def __init_groups(self):
        for _ in range(settings.peer_groups):
            self.__groups.append([])

    def __clean_groups(self):
        for group_index in range(len(self.__groups)):
            alive_group_tmp = []
            for connection in self.__groups[group_index]:
                if connection.last_request_is_time_out():
                    connection.shutdown()
                    continue
                alive_group_tmp.append(connection)
            self.__groups[group_index] = alive_group_tmp

    def __join_groups(self):
        return list(itertools.chain.from_iterable(self.__groups))

    def __get_connection_group(self, connection):
        for group in self.__groups:
            if connection in group:
                return group
        return None

    def __get_waiting_connection_from_group(self, group):
        waiting_group = []
        for connection in group:
            if connection.state == 'waiting':
                waiting_group.append(connection)
        return waiting_group

    def find_neighbour(self, connection):
        # FIXME
        self.__clean_groups()
        for group in self.__groups:
            if self.__peer_has_connection_to_group(group, connection):
                continue
            waiting_group = self.__get_waiting_connection_from_group(group)
            waiting_group = self.__remove_peer_from_group(waiting_group, connection)
            if len(waiting_group) == 0:
                continue
            return waiting_group[0]
        return None

    def __remove_peer_from_group(self, group, connection):
        if connection in group:
            group.remove(connection)
        return group

    def __peer_has_connection_to_group(self, group, connection):
        return self.__groups.index(group) in connection.groups

    def save_connection(self, connection):
        connection.state = 'waiting'
        if not self.__get_connection_group(connection) is None:
            self.__update_connection(connection)
            self.update_state(connection, 'waiting')
            return
        self.__put_connection_in_group(connection)

    def __put_connection_in_group(self, connection):
        connection.state = 'waiting'
        connection.groups = set()
        groups_size_list = list(map(len, self.__groups))
        min_size = min(groups_size_list)
        min_group_index = groups_size_list.index(min_size)
        self.__groups[min_group_index].append(connection)

    def __update_connection(self, new_connection):
        group = self.__join_groups()
        connection_index = group.index(new_connection)
        save_connection = group[connection_index]
        save_connection.update_request(new_connection)

    def get_all_connections(self):
        self.__clean_groups()
        group_all = self.__join_groups()
        return group_all

    def update_neighbour_group(self, connection0, connection1):
        if connection0 is None or connection1 is None:
            return
        connection0_group_index = self.__get_connection_group_index(connection0)
        connection1_group_index = self.__get_connection_group_index(connection1)
        connection0.groups.add(connection0_group_index)
        connection1.groups.add(connection1_group_index)

    def update_state(self, connection, state):
        if connection is None:
            return
        connection.state = state

    def __get_connection_group_index(self, connection):
        for index in range(len(self.__groups)):
            if connection in self.__groups[index]:
                return index

    def can_be_disconnected(self, connection):
        group = self.__get_connection_group(connection)
        connection_groups = connection.groups
        group_has_enough_connections = len(group) > settings.peer_connections
        connection_connected_to_all_groups  = len(connection_groups) == len(self.__groups)
        return group_has_enough_connections and connection_connected_to_all_groups

    def disconnect(self, connection):
        group = self.__get_connection_group(connection)
        group.remove(connection)
        connection.shutdown()

    def shutdown(self):
        for index in range(len(self.__groups)):
            for connection in self.__groups[index]:
                connection.shutdown()
            self.__groups[index] = []
