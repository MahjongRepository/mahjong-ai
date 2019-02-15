# -*- coding: utf-8 -*-


class OwnHandProtocol:
    tiles_unique = 34
    tiles_num = tiles_unique * 4
    input_size = tiles_num

    def __init__(self):
        self.input_data = []
        self.output_data = []

    def parse_new_data(self, raw_data):
        for index, row in raw_data:
            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            if not waiting_temp:
                continue

            tiles = [0 for x in range(self.tiles_num)]
            waiting = [0 for x in range(self.tiles_unique)]

            for x in waiting_temp:
                if not x:
                    continue

                temp = x.split(';')
                tile = int(temp[0]) // 4
                waiting[tile] = 1

            player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]
            for i in range(len(player_hand)):
                tiles[player_hand[i]] = 1

            self.input_data.append(tiles)
            self.output_data.append(waiting)
