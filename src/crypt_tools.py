# -*- coding: utf-8 -*-
__author__ = 'Akinava'
__author_email__ = 'akinava@gmail.com'
__copyright__ = 'Copyright © 2019'
__license__ = 'MIT License'
__version__ = [0, 0]


import os
import json
from cryptotool import *
import settings
from utilit import Singleton
from settings import logger


class Tools(Singleton):
    priv_key_length = 32
    pub_key_length = 64
    fingerprint_length = 32
    sign_length = 64

    def __init__(self):
        logger.debug('')
        self.__init_ecdsa()

    def __init_ecdsa(self):
        logger.debug('')
        if self.__get_ecdsa_from_file():
            return
        self.__generate_new_ecdsa()
        self.__save_ecdsa()

    def __read_shadow_file(self):
        logger.info(settings.shadow_file)
        if not os.path.isfile(settings.shadow_file):
            return None
        with open(settings.shadow_file) as shadow_file:
            try:
                return json.loads(shadow_file.read())
            except json.decoder.JSONDecodeError:
                return None

    def __save_shadow_file(self, data):
        logger.debug('')
        with open(settings.shadow_file, 'w') as shadow_file:
            shadow_file.write(json.dumps(data, indent=2))

    def __update_shadow_file(self, new_data):
        logger.debug('')
        file_data = {} or self.__read_shadow_file()
        if file_data is None:
            file_data = {}
        file_data.update(new_data)
        self.__save_shadow_file(file_data)

    def __get_ecdsa_from_file(self):
        logger.debug('')
        shadow_data = self.__read_shadow_file()
        if shadow_data is None:
            return False
        ecdsa_priv_key_b58 = shadow_data.get('ecdsa', {}).get('key')
        if ecdsa_priv_key_b58 is None:
            return False
        ecdsa_priv_key = B58().unpack(ecdsa_priv_key_b58)
        self.ecdsa = ECDSA(priv_key=ecdsa_priv_key)
        return True

    def __generate_new_ecdsa(self):
        logger.debug('')
        self.ecdsa = ECDSA()

    def __save_ecdsa(self):
        logger.debug('')
        ecdsa_priv_key = self.ecdsa.get_priv_key()
        ecdsa_priv_key_b58 = B58().pack(ecdsa_priv_key)
        fingerprint_b58 = B58().pack(self.get_fingerprint())
        self.__update_shadow_file(
            {'ecdsa': {
                'key': ecdsa_priv_key_b58,
                'fingerprint': fingerprint_b58}}
        )

    def get_fingerprint(self):
        logger.debug('')
        if not hasattr(self, 'fingerprint'):
            self.__make_fingerprint()
        return self.fingerprint

    def get_fingerprint_len(self):
        return self.fingerprint_length

    def __make_fingerprint(self):
        open_key = self.ecdsa.get_pub_key()
        self.fingerprint = sha256(open_key)

    def sign_message(self, message):
        return self.ecdsa.sign(message) + self.ecdsa.get_pub_key()
