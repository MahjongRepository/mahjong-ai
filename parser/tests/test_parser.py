# -*- coding: utf-8 -*-
import os
import unittest

from src.log_parser import LogParser


class ClientTestCase(unittest.TestCase):

    def test_parse_hands_number(self):
        parser = LogParser()
        log_content = self._load_data('simple_hanchan.xml')
        hands_data = parser.get_game_hands(log_content, 'id')
        self.assertEqual(len(hands_data), 9)

    def _load_data(self, file_name):
        data_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)),
            'resources',
            file_name
        )

        with open(data_path, 'r') as f:
            return f.read()
