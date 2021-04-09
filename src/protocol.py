# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import sys
from settings import logger
import crypt_tools
from connection import Connection


class GeneralProtocol:
    def __init__(self, message=None, on_con_lost=None):
        logger.debug('')
        self.crypt_tools = crypt_tools.Tools()
        self.response = message
        self.on_con_lost = on_con_lost
        self.transport = None

    def connection_made(self, transport):
        logger.debug('')
        self.transport = transport
        self.send_message()

    def send_message(self, addr=None):
        if not self.response is None:
            logger.debug('')
            self.transport.sendto(self.response, addr)

    def datagram_received(self, request, addr):
        logger.info('request %s from %s' % (request, addr))
        connection = Connection()
        connection.datagram_received(request, addr, self.transport)
        self.response = self.handle(connection)
        self.send_message(addr)
        if not self.response is None:
            print('response "%s"' % (self.response))

    def connection_lost(self, addr):
        logger.debug('')
        # TODO remove this connections
        pass

    def handle(self, connection):
        logger.debug('')
        # TODO make a tread
        request_name = self.define_request(connection)
        logger.info('GeneralProtocol function defined as {}'.format(request_name))
        if request_name is None:
            return
        response_function = self.get_response_function(request_name)
        if response_function is None:
            return
        return response_function(connection)

    def define_request(self, connection):
        logger.debug('')
        self_functions = dir(self)
        for function_name in self_functions:
            if function_name == sys._getframe().f_code.co_name:
                continue
            if not 'define_' in function_name:
                continue
            define_function = getattr(self, function_name)
            if not define_function(connection) is True:
                continue
            request_name = function_name.replace('define_', '')
            return request_name
        logger.warn('GeneralProtocol can not define request')

    def get_response_function(self, request_name):
        response_name = self.protocol[request_name]
        logger.info('GeneralProtocol response_name {}'.format(response_name))
        response_function_name = 'do_{}'.format(response_name)
        logger.info('GeneralProtocol response_function_name {}'.format(response_function_name))
        if not hasattr(self, response_function_name):
            return
        return getattr(self, response_function_name)

    def define_swarm_ping(self, connection):
        if connection.get_request() == '':
            return True
        return False

    def define_swarm_peer_request(self, connection):
        check_request_len = self.crypt_tools.get_fingerprint_len() * 2 == len(connection.get_request())
        check_fingerprint = connection.get_request()[: self.crypt_tools.get_fingerprint_len()] == self.crypt_tools.get_fingerprint()
        return check_request_len and check_fingerprint

    def do_swarm_ping(self):
        return ''
