# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import json
import os
import sys
import random
import struct
import logging
import settings
import get_args


def setup_logger():
    settings.logger = logging.getLogger(__name__)
    settings.logger.setLevel(settings.logging_level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(settings.logging_format)
    handler.setFormatter(formatter)
    settings.logger.addHandler(handler)


def read_config_file():
    with open(settings.config_file, 'r') as cfg_file:
        return json.loads(cfg_file.read())

def import_config():
    options, args = get_args.parser()
    options_keys = vars(options)
    config = read_config_file()
    for k, v in config.items():
        if k in options_keys:
            continue
        setattr(settings, k, v)


def import_options():
    options, args = get_args.parser()
    for key in vars(options):
        value = getattr(options, key)
        if value is None:
            continue
        setattr(settings, key, value)


def setup_settings():
    setup_logger()
    import_options()
    import_config()


def get_rundom_server():
    peers = read_peers_from_file()
    servers = filter_peers(peers, 'server')
    return get_rundom_peer(servers)


def filter_peers(peers, filter):
    filtered_peers = []
    for peer in peers:
        if peer['type'] != filter:
            continue
        filtered_peers.append(peer)
    return filtered_peers


def read_peers_from_file():
    with open(settings.peers_file, 'r') as f:
        return json.loads(f.read())


def get_rundom_peer(peers):
    return random.choice(peers)


def pack_host(host):
    return ''.join(map(chr, (map(int, map(str, host.split('.')))))).encode()

def pack_port(port):
    return struct.pack('H', port)

def binary_not(b):
    return 1 - b

def unpack_stream(data, length):
    return data[ :length], data[length: ]
