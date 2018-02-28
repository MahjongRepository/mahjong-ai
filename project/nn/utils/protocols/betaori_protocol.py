# -*- coding: utf-8 -*-
import csv
import itertools

tiles_unique = 34
tiles_num = tiles_unique * 4
input_size = tiles_num * 5 + tiles_num * 5 * 2 + tiles_num + tiles_num // 4


class BetaoriProtocol(object):
    def __init__(self):
        self.input_data = []
        self.output_data = []
        self.verification_data = []

    @staticmethod
    def process_discards(discards_data, melds_data, out_tiles):
        # For input we concatenate 5 rows of data for each player,
        # each row representing 136 tiles and their states:
        # First row - is discarded
        # Seconds row - tsumogiri flag
        # Third row - "after meld" flag
        # Fourth row - tile is present in open set
        # Fifth row - how long ago tile was discarded, 1 for first discad,
        #             and decreases by 0.025 for each following discard
        # NB: this should correspond to input_size variable!
        discards = [0 for x in range(tiles_num)]
        tsumogiri = [0 for x in range(tiles_num)]
        after_meld = [0 for x in range(tiles_num)]
        melds = [0 for x in range(tiles_num)]
        discards_order = [0 for x in range(tiles_num)]

        discard_order_value = 1
        discard_order_step = 0.025

        discards_temp = BetaoriProtocol.prepare_discards(discards_data)
        for x in discards_temp:
            tile = x[0]
            is_tsumogiri = x[1]
            is_after_meld = x[2]

            discards[tile] = 1
            tsumogiri[tile] = is_tsumogiri
            after_meld[tile] = is_after_meld
            discards_order[tile] = discard_order_value
            discard_order_value -= discard_order_step

            out_tiles[tile // 4] += 0.25

        melds_temp = BetaoriProtocol.prepare_melds(melds_data)
        for x in melds_temp:
            tiles = x[0]
            for tile in tiles:
                melds[tile] = 1

                out_tiles[tile // 4] += 0.25

        return discards, tsumogiri, after_meld, melds, discards_order, out_tiles

    @staticmethod
    def prepare_discards(data):
        # sometimes we have empty discards
        # for example when other player is tenpai after first discard
        if not data:
            return []

        discards_temp = [x for x in data.split(',')]
        result = []
        for x in discards_temp:
            temp = x.split(';')
            result.append([
                # tile
                int(temp[0]),
                # is_tsumogiri
                int(temp[1]),
                # is_after_meld
                int(temp[2])
            ])
        return result

    @staticmethod
    def prepare_melds(data):
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

    def parse_new_data(self, raw_data):
        for row in raw_data:
            # total number of out tiles (all discards, all melds, player hand, dora indicators)
            out_tiles = [0 for x in range(tiles_num // 4)]

            discards, tsumogiri, after_meld, melds, discards_order, out_tiles = BetaoriProtocol.process_discards(
                row['tenpai_player_discards'],
                row['tenpai_player_melds'],
                out_tiles
            )

            sp_discards, sp_tsumogiri, sp_after_meld, sp_melds, sp_discards_order, out_tiles = BetaoriProtocol.process_discards(
                row['second_player_discards'],
                row['second_player_melds'],
                out_tiles
            )

            tp_discards, tp_tsumogiri, tp_after_meld, tp_melds, tp_discards_order, out_tiles = BetaoriProtocol.process_discards(
                row['third_player_discards'],
                row['third_player_melds'],
                out_tiles
            )

            player_hand = [0 for x in range(tiles_num)]
            for x in [int(x) for x in row['player_hand'].split(',')]:
                player_hand[x] += 1

                out_tiles[x // 4] += 0.25

            for x in [int(x) for x in row['dora_indicators'].split(',')]:
                out_tiles[x // 4] += 0.25

            input_cur = list(itertools.chain(
                discards,
                tsumogiri,
                after_meld,
                melds,
                discards_order,
                sp_discards,
                sp_tsumogiri,
                sp_after_meld,
                sp_melds,
                sp_discards_order,
                tp_discards,
                tp_tsumogiri,
                tp_after_meld,
                tp_melds,
                tp_discards_order,
                player_hand,
                out_tiles,
            ))

            if len(input_cur) != input_size:
                print("Internal error: len(input_cur) should be %d, but is %d" % (input_size, len(input_cur)))
                exit(1)

            self.input_data.append(input_cur)

            # Output etalon - actual waits
            # For tiles that are not 100% safe and not actual waits,
            # we give value 0
            waiting = [0 for x in range(tiles_num // 4)]

            tenpai_discards = BetaoriProtocol.prepare_discards(row['tenpai_player_discards'])
            tenpai_melds = BetaoriProtocol.prepare_melds(row['tenpai_player_melds'])

            for x in tenpai_discards:
                # Here we give hint to network during training: tiles from discard
                # give output "-1":
                waiting[x[0] // 4] = -1

            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            for x in waiting_temp:
                temp = x.split(';')
                tile = int(temp[0])
                # if cost == 0 it avgs that player can't win on this waiting
                # TODO: currently ignored
                # cost = int(temp[1])
                waiting[tile // 4] = 1

            self.output_data.append(waiting)

            # Use it only for visual debugging!
            tenpai_player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]
            verification_cur = [
                tenpai_player_hand,
                tenpai_discards,
                tenpai_melds,
                waiting_temp
            ]

            self.verification_data.append(verification_cur)
