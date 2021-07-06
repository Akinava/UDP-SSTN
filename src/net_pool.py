# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import itertools
import settings
from utilit import Singleton
from settings import logger


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
                if connection.last_received_message_is_over_time_out():
                    logger.debug('host {} disconnected bt timeout'.format(connection))
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
        for connection in group:
            if connection.state == 'waiting':
                return connection

    def find_neighbour(self, connection):
        self.__clean_groups()
        for group in self.__groups:
            if self.__peer_has_connection_to_group(group, connection):
                continue
            waiting_group = self.__remove_peer_from_group(group, connection)
            waiting_connection = self.__get_waiting_connection_from_group(waiting_group)
            return waiting_connection

    def __remove_peer_from_group(self, group, connection):
        if connection in group:
            connection_index = group.index(connection)
            return group[: connection_index] + group[connection_index+1:]
        return group

    def __peer_has_connection_to_group(self, group, connection):
        return self.__groups.index(group) in connection.groups

    def save_connection(self, connection):
        self.update_state(connection, 'waiting')
        if not self.__get_connection_group(connection) is None:
            self.__update_connection_in_group(connection)
        else:
            self.__put_connection_in_group(connection)

    def __put_connection_in_group(self, connection):
        logger.info('')
        def find_small_group():
            groups_size_list = list(map(len, self.__groups))
            min_size = min(groups_size_list)
            min_group_index = groups_size_list.index(min_size)
            return self.__groups[min_group_index]
        connection.groups = set()
        group = find_small_group()
        group.append(connection)

    def __update_connection_in_group(self, new_connection):
        logger.info('')
        group = self.__get_connection_group(new_connection)
        connection_index = group.index(new_connection)
        old_connection = group[connection_index]
        self.__copy_connection_property(new_connection, old_connection)
        group[connection_index] = new_connection

    def __copy_connection_property(self, new_connection, old_connection):
        new_connection.set_pub_key(old_connection.get_pub_key())
        new_connection.set_encrypt_marker(old_connection.get_encrypt_marker())
        new_connection.groups = old_connection.groups
        new_connection.set_time_sent_message(old_connection.get_time_sent_message())

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
        group_has_enough_connections = len(group) > settings.peer_connections
        connection_connected_to_all_groups = len(connection.groups) == len(self.__groups)
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
