# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


from crypt_tools import Tools as CryptTools


PROTOCOL = {
    'server_protocol_version': __version__,
    'package' : [
        {
            'name': 'swarm_ping',
            'define': 'define_swarm_ping',
        },
        {
            'name': 'swarm_peer_request',
            'package_id_marker': 1,
            'define': [
                'verify_len_swarm_peer_request',
                'verify_package_id_marker',
                'verify_timestamp',
                'verify_my_fingerprint',
            ],
            'response': 'swarm_peer',
            'structure': [
                {'name': 'protocol_version', 'length': 1, 'type': 'int'},
                {'name': ('encrypted_request_marker', 'package_id_marker'), 'length': 1},
                {'name': 'timestamp', 'length': 4, 'type': 'timestamp'},
                {'name': 'my_fingerprint', 'length': CryptTools.fingerprint_length},
                {'name': 'connection_open_key', 'length': CryptTools.pub_key_length},
            ]
        },
        {
            'name': 'swarm_peer',
            'package_id_marker': 2,
            'structure': [
                {'name': 'package_id_marker', 'length': 1},
                {'name': 'neighbour_open_key', 'length': CryptTools.pub_key_length},
                {'name': 'neighbour_addr', 'length': 4 + 2},
                {'name': 'disconnect_flag', 'length': 1, 'type': 'bool'},
                {'name': 'timestamp', 'length': 4, 'type': 'timestamp'},
                {'name': 'receiver_fingerprint', 'length': CryptTools.fingerprint_length},
            ]
        }
    ],
    'markers': [
        {'name': 'encrypted_request_marker', 'start bit': 0, 'length': 1, 'type': 'bool_marker'},
        {'name': 'package_id_marker', 'start bit': 1, 'length': 7},
        {'name': 'major_version_marker', 'start bit': 0, 'length': 4},
        {'name': 'minor_version_marker', 'start bit': 4, 'length': 4},
    ]
}
