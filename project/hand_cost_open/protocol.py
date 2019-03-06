import itertools

from base.protocol import Protocol
from hand_cost_open.exporter import OpenHandCostCSVExporter


class OpenHandCostProtocol(Protocol):
    tiles_unique = 34
    tiles_num = tiles_unique * 4

    input_size = tiles_unique * 6
    output_size = 9

    exporter = OpenHandCostCSVExporter

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

    def parse_new_data(self, raw_data):
        for index, row in raw_data:
            # total number of out tiles (all discards, all melds, player hand, dora indicators)
            out_tiles = [0 for x in range(self.tiles_unique)]
            defending_hand = []

            discards, tsumogiri, after_meld, melds, discards_last, discards_second_last, out_tiles = self.process_discards(
                row['tenpai_player_discards'],
                row['tenpai_player_melds'],
                out_tiles
            )

            sp_discards, sp_tsumogiri, sp_after_meld, sp_melds, sp_discards_last, sp_discards_second_last, out_tiles = self.process_discards(
                row['second_player_discards'],
                row['second_player_melds'],
                out_tiles
            )

            tp_discards, tp_tsumogiri, tp_after_meld, tp_melds, tp_discards_last, tp_discards_second_last, out_tiles = self.process_discards(
                row['third_player_discards'],
                row['third_player_melds'],
                out_tiles
            )

            for x in [int(x) for x in row['player_hand'].split(',')]:
                defending_hand.append(x // 4)
                out_tiles[x // 4] += 1

            dora_indicators = [int(x) for x in str(row['dora_indicators']).split(',')]
            for x in dora_indicators:
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

            if len(input_data) != self.input_size:
                print('Internal error: len(input_data) should be {}, but is {}'.format(
                    self.input_size,
                    len(input_data)
                ))
                exit(1)

            self.input_data.append(input_data)

            tenpai_discards = self.prepare_discards(row['tenpai_player_discards'])
            tenpai_melds = self.prepare_melds(row['tenpai_player_melds'])

            # let's find maximum hand cost for now
            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            waiting = None
            waiting_index = 0
            for x in waiting_temp:
                temp = x.split(';')

                if temp[2] == 'None':
                    continue

                tile = int(temp[0])
                han = int(temp[2])
                fu = int(temp[3])

                if not waiting:
                    waiting = [tile, han, fu]

                key = OpenHandCostProtocol.create_hand_cost_key(han, fu)

                index = self.hand_cost_mapping.get(key)
                if index > waiting_index:
                    waiting = [tile, han, fu]
                    waiting_index = index

            self.output_data.append(waiting_index)

            # Use it only for visual debugging!
            tenpai_player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]
            verification_data = [
                tenpai_player_hand,
                tenpai_discards,
                tenpai_melds,
                waiting,
                defending_hand,
                dora_indicators,
            ]

            self.verification_data.append(verification_data)

    @staticmethod
    def create_hand_cost_key(han, fu):
        if fu >= 60:
            han += 1

        if han >= 5:
            key = str(han)
        elif han >= 13:
            han = 13
            key = str(han)
        else:
            key = '{}-{}'.format(han, fu)

        return key

