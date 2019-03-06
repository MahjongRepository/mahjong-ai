import itertools

from hand_cost_open.exporter import OpenHandCostCSVExporter


class OpenHandCostProtocol:
    tiles_unique = 34
    tiles_num = tiles_unique * 4

    input_size = tiles_unique * 6
    output_size = 9

    exporter = OpenHandCostCSVExporter

    def __init__(self):
        self.input_data = []
        self.output_data = []
        self.verification_data = []

    def parse_new_data(self, raw_data):
        for index, row in raw_data:
            # total number of out tiles (all discards, all melds, player hand, dora indicators)
            out_tiles = [0 for x in range(OpenHandCostProtocol.tiles_unique)]
            defending_hand = []

            discards, tsumogiri, after_meld, melds, discards_last, discards_second_last, out_tiles = OpenHandCostProtocol.process_discards(
                row['tenpai_player_discards'],
                row['tenpai_player_melds'],
                out_tiles
            )

            sp_discards, sp_tsumogiri, sp_after_meld, sp_melds, sp_discards_last, sp_discards_second_last, out_tiles = OpenHandCostProtocol.process_discards(
                row['second_player_discards'],
                row['second_player_melds'],
                out_tiles
            )

            tp_discards, tp_tsumogiri, tp_after_meld, tp_melds, tp_discards_last, tp_discards_second_last, out_tiles = OpenHandCostProtocol.process_discards(
                row['third_player_discards'],
                row['third_player_melds'],
                out_tiles
            )

            for x in [int(x) for x in row['player_hand'].split(',')]:
                defending_hand.append(x // 4)
                out_tiles[x // 4] += 1

            for x in [int(x) for x in str(row['dora_indicators']).split(',')]:
                out_tiles[x // 4] += 1

            out_tiles_0 = [1 if x >= 1 else 0 for x in out_tiles]
            out_tiles_1 = [1 if x >= 2 else 0 for x in out_tiles]
            out_tiles_2 = [1 if x >= 3 else 0 for x in out_tiles]
            out_tiles_3 = [1 if x == 4 else 0 for x in out_tiles]

            input_data = list(itertools.chain(
                discards,
                melds,
                out_tiles_0,
                out_tiles_1,
                out_tiles_2,
                out_tiles_3,
            ))

            if len(input_data) != OpenHandCostProtocol.input_size:
                print('Internal error: len(input_data) should be {}, but is {}'.format(
                    OpenHandCostProtocol.input_size,
                    len(input_data)
                ))
                exit(1)

            self.input_data.append(input_data)

            tenpai_discards = OpenHandCostProtocol.prepare_discards(row['tenpai_player_discards'])
            tenpai_melds = OpenHandCostProtocol.prepare_melds(row['tenpai_player_melds'])

            hand_cost_scale = [0 for _ in range(self.output_size)]

            hand_cost_mapping = {
                '1-30': 0,
                '1-40': 0,
                '1-50': 0,
                '2-25': 1,
                '2-30': 1,
                '2-40': 1,
                '2-50': 1,
                '3-25': 2,
                '3-30': 2,
                '3-40': 2,
                '3-50': 2,
                '3-60': 3,
                '4-25': 3,
                '4-30': 3,
                '4-40': 4,
                '4-50': 4,
                '5': 4,
                '6': 5,
                '7': 5,
                '8': 6,
                '9': 6,
                '10': 6,
                '11': 7,
                '12': 7,
                '13': 8,
            }

            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            for x in waiting_temp:
                temp = x.split(';')

                if temp[2] == 'None':
                    continue

                han = int(temp[2])
                fu = int(temp[3])

                if fu >= 60:
                    han += 1

                if han >= 5:
                    key = str(han)
                elif han >= 13:
                    han = 13
                    key = str(han)
                else:
                    key = '{}-{}'.format(han, fu)

                hand_cost_scale[hand_cost_mapping.get(key)] = 1

            self.output_data.append(hand_cost_scale)

            # Use it only for visual debugging!
            tenpai_player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]
            verification_data = [
                tenpai_player_hand,
                tenpai_discards,
                tenpai_melds,
                waiting_temp,
                defending_hand
            ]

            self.verification_data.append(verification_data)

    @staticmethod
    def process_discards(discards_data, melds_data, out_tiles):
        # For input we concatenate 5 rows of data for each player,
        # each row representing 136 tiles and their states:
        # First row - is discarded
        # Seconds row - tsumogiri flag
        # Third row - "after meld" flag
        # Fourth row - tile is present in open set
        # Fifth row - how long ago tile was discarded, 1 for first discard,
        #             and decreases by 0.025 for each following discard
        # NB: this should correspond to input_size variable!
        discards = [0 for x in range(OpenHandCostProtocol.tiles_unique)]
        tsumogiri = [1 for x in range(OpenHandCostProtocol.tiles_unique)]
        after_meld = [0 for x in range(OpenHandCostProtocol.tiles_unique)]
        melds = [0 for x in range(OpenHandCostProtocol.tiles_unique)]
        discards_last = [0 for x in range(OpenHandCostProtocol.tiles_unique)]
        discards_second_last = [0 for x in range(OpenHandCostProtocol.tiles_unique)]

        discards_temp = OpenHandCostProtocol.prepare_discards(discards_data)
        for x in discards_temp:
            tile = x[0] // 4
            is_tsumogiri = x[1]
            is_after_meld = x[2]
            after_riichi = x[3]
            taken_for_meld = x[4]

            discards[tile] = 1
            if is_tsumogiri == 1:
                tsumogiri[tile] = is_tsumogiri
            if after_meld[tile] == 0:
                after_meld[tile] = is_after_meld

            out_tiles[tile] += 1

        is_last = True
        for x in reversed(discards_temp):
            tile = x[0] // 4
            is_tsumogiri = x[1]

            if is_last:
                if is_tsumogiri == 0:
                    discards_last[tile] = 1
                    is_last = False
                    continue
                else:
                    continue
            else:
                if is_tsumogiri == 0:
                    discards_second_last[tile] = 1
                    break
                else:
                    continue

        melds_temp = OpenHandCostProtocol.prepare_melds(melds_data)
        for x in melds_temp:
            tiles = x[0]
            for tile in tiles:
                tile = tile // 4
                melds[tile] = 1
                out_tiles[tile] += 1

        return discards, tsumogiri, after_meld, melds, discards_last, discards_second_last, out_tiles

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
                int(temp[2]),
                # after riichi
                int(temp[3]),
                # was taken for meld
                int(temp[4]),
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

