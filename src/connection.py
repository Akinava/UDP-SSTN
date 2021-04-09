# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import struct
from time import time
from utilit import Singleton
import settings
from settings import logger


class Connection:
    def __init__(self):
        self.set_last_response()

    def set_last_response(self):
        self.last_response = time()

    def loads(self, connection_data):
        for key, val in connection_data.items():
            if key in ['host', 'port']:
                key = 'remote_{}'.format(key)
            setattr(self, key, val)
        return self

    def is_alive(self):
        if self.transport.is_closing():
            return False
        return True

    def is_time_out(self):
        return time() - self.last_response > settings.peer_timeout_seconds

    def set_net(self, net):
        self.net = net

    def shutdown(self):
        self.net.remove(self)

    def set_transport(self, transport):
        self.transport = transport

    def set_protocol(self, protocol):
        self.protocol = protocol

    def set_local_port(self, local_port):
        self.local_port = local_port

    def get_remote_addr(self):
        return self.remote_host, self.remote_port

    def dump_addr(self):
        return struct.pack('>BBBBH', *(map(int, self.remote_host.split('.'))), self.remote_port)

    def load_addr(self, data):
        port = struct.unpack('>H', data[4:6])
        ip_map = struct.unpack('>BBBB', data[0:4])
        ip = '.'.join(map, ip_map)
        return ip, port

    def __eq__(self, connection):
        if self.remote_host != connection.remote_host:
            return False
        if self.remote_port != connection.remote_port:
            return False
        return True

    def set_listener(self, local_port, transport, protocol):
        self.set_protocol(protocol)
        self.set_transport(transport)
        self.set_local_port(local_port)

    def set_remote_host(self, remote_host):
        self.remote_host = remote_host

    def get_remote_host(self):
        return self.remote_host

    def set_remote_port(self, remote_port):
        self.remote_port = remote_port

    def get_remote_port(self):
        return self.remote_port

    def set_request(self, request):
        self.request = request

    def get_request(self):
        return self.request

    def get_fingerprint(self):
        return self.fingerprint

    def set_remote_addr(self, addr):
        self.set_remote_host(addr[0])
        self.set_remote_port(addr[1])

    def close_transport(self):
        self.transport.close()

    def datagram_received(self, request, remote_addr, transport):
        self.set_remote_addr(remote_addr)
        self.set_request(request)
        self.set_transport(transport)

    def set_fingerprint(self, fingerprint):
        self.fingerprint = fingerprint

    def send(self, response):
        logger.info('')
        print(response, (self.remote_host, self.remote_port))
        self.transport.sendto(response, (self.remote_host, self.remote_port))


class NetPool(Singleton):
    def __init__(self):
        self.group_0, self.group_1 = {}, {}
