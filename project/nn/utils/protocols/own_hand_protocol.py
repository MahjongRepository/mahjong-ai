# -*- coding: utf-8 -*-
import csv
import itertools

tiles_unique = 34
tiles_num = tiles_unique * 4


class OwnHandProtocol(object):

    def __init__(self):
        self.input_data = []
        self.output_data = []

    def parse_new_data(self, raw_data):
        for row in raw_data:
            if not row['tenpai_player_waiting']:
                continue

            player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]

            waiting = [0 for x in range(tiles_unique)]
            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            for x in waiting_temp:
                temp = x.split(';')
                tile = int(temp[0]) // 4
                waiting[tile] = 1

            tiles = [0 for x in range(tiles_num)]
            for i in range(len(player_hand)):
                tiles[player_hand[i]] = 1

            self.input_data.append(tiles)
            self.output_data.append(waiting)
