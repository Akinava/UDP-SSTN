# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import struct
import time
from utilit import NULL


class Parser:
    struct_length = {
        1: 'B',
        2: 'H',
        4: 'I',
        8: 'Q',
    }
    struct_addr = '>BBBBH'

    def __init__(self, protocol):
        self.__protocol = protocol

    def set_package_protocol(self, package_protocol):
        self.package_protocol = package_protocol

    def find_protocol_package(self, package_name):
        for package_protocol in self.__protocol:
            if package_protocol['name'] == package_name:
                return package_protocol
        raise Exception('Error: no protocol with the name {}'.format(package_name))

    def set_connection(self, connection):
        self.connection = connection

    def unpack(self):
        package = {}
        data = self.connection.get_request()
        package_structure = self.package_protocol['structure']
        for part_structure in package_structure:
            part_name = part_structure['name']
            part_data, data = self.__unpack_stream(data, part_structure['length'])
            part_data = self.set_type(part_data, part_structure)
            package[part_name] = part_data
            self.__unpack_markers(part_name, package)
        return package

    def set_type(self, part_data, part_structure):
        part_type = part_structure.get('type', NULL())
        if part_type is NULL():
            return part_data
        set_type_function = getattr(self, 'unpack_{}'.format(part_type))
        return set_type_function(part_data)

    def unpack_timestamp(self, part_data):
        return self.unpack_int(part_data)

    def unpack_bool_marker(self, part_data):
        return part_data == 1

    def pack_bool(self, part_data):
        return b'\xff' if part_data else b'\x00'

    def get_part(self, name):
        return self.unpack(self.connection, self.package_protocol).get(name, NULL())

    def calc_requared_length(self, package_protocol):
        length = 0
        structure = package_protocol.get('request_protocol')
        if structure is None:
            return length
        for part in structure:
            length += part['length']
        return length

    def pack_addr(self, addr):
        host, port = addr
        return struct.pack(self.struct_addr, *(map(int, host.split('.'))), port)

    def get_packed_addr_length(self):
        return struct.calcsize(self.struct_addr)

    def pack_timestemp(self):
        return self.pack_int(int(time.time()), 4)

    def __unpack_markers(self, part_name, package):
        if not isinstance(part_name, tuple):
            return
        for marker_name in part_name:
            marker_structure = self.__get_marker_description(marker_name)
            marker_data = self.set_type(marker_data, marker_structure)
            marker_data = self.__unpack_marker(marker_structure, markers_packed_data)
            package[marker_name] = marker_data
        del package[markers]

    def __unpack_marker(self, marker_structure, marker_packed_data):
        marker_packed_data_length = len(markers_packed_data)
        marker_mask = self.__make_mask(marker_structure['start bit'], marker_structure['length'], marker_packed_data_length)
        left_shift = self.__get_left_shift(marker_structure['start bit'], marker_structure['length'], marker_packed_data_length)
        marker_packed_int = self.unpack_int(marker_packed_data)
        marker_data = marker_packed_int & marker_mask
        return marker_data >> left_shift

    def __make_mask(self, start_bit, length_bit, length_data_byte):
        return  ((1 << length_bit) - 1) << 8 * length_data_byte - start_bit - length_bit

    def __get_left_shift(self, start_bit, length_bit, length_data_byte):
        return length_data_byte * 8 - start_bit - length_bit

    def __get_marker_description(self, marker_name):
        for marker_description in self.__protocol.get('markers', []):
            if marker_description['name'] == marker_name:
                return marker_description
        raise Exception('Error: no description for marker {}'.format(marker_name))

    def unpack_int(self, data):
        return struct.unpack('>' + self.struct_length[len(data)], data)[0]

    def pack_int(self, data, size):
        return struct.pack('>' + self.struct_length[size], data)

    def __unpack_stream(self, data, length):
        return data[ :length], data[length: ]
