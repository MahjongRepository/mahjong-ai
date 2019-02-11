# -*- coding: utf-8 -*-
import itertools


class OwnHandProtocol:
    tiles_unique = 34
    tiles_num = tiles_unique * 4
    input_size = tiles_num * 2

    def __init__(self):
        self.input_data = []
        self.output_data = []

    def parse_new_data(self, raw_data):
        for index, row in raw_data:
            melds = [0 for x in range(self.tiles_num)]
            tiles = [0 for x in range(self.tiles_num)]

            waiting = [0 for x in range(self.tiles_unique)]
            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            for x in waiting_temp:
                temp = x.split(';')
                tile = int(temp[0]) // 4
                waiting[tile] = 1

            player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]
            for i in range(len(player_hand)):
                tiles[player_hand[i]] = 1

            melds_temp = self.prepare_melds(row['tenpai_player_melds'])
            for x in melds_temp:
                meld_tiles = x[0]
                for tile in meld_tiles:
                    melds[tile] = 1

            input_cur = list(itertools.chain(
                tiles,
                melds
            ))

            if len(input_cur) != self.input_size:
                print("Internal error: len(input_cur) should be %d, but is %d" % (self.input_size, len(input_cur)))
                exit(1)

            self.input_data.append(input_cur)
            self.output_data.append(waiting)

    def prepare_melds(self, data):
        melds = []
        melds_temp = [x for x in data.split(',') if x]
        for x in melds_temp:
            temp = x.split(';')
            tiles = [int(x) for x in temp[1].split('/')]
            melds.append([
                tiles,
                # meld type
                temp[0]
            ])
        return melds
