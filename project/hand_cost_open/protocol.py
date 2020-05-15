import itertools

from mahjong.constants import EAST, NORTH, SOUTH, WEST
from mahjong.utils import is_aka_dora, plus_dora

from base.protocol import Protocol


def prepare_closed_hand_input(
    round_wind,
    dora_indicators,
    player_closed_hand,
    player_melds,
    player_discards,
    tenpai_player_wind,
    tenpai_player_riichi,
    tenpai_player_melds,
    tenpai_player_discards,
    second_player_melds,
    second_player_discards,
    third_player_melds,
    third_player_discards,
):
    """
    meld dict format = {
        'tiles': List of 136 format tiles
    }

    discard dict format = {
        'tile': 136 format,
        'is_tsumogiri': bool,
        'is_after_meld': bool,
    }

    :param round_wind:                27 (east), 28 (south), 29 (west), 30 (north)
    :param dora_indicators:           List of 136 format tiles
    :param player_closed_hand:        Our player. List of 136 format tiles
    :param player_melds:              Our player. List of meld dicts
    :param player_discards:           Our player. List of discard dicts
    :param tenpai_player_wind:        27 (east), 28 (south), 29 (west), 30 (north)
    :param tenpai_player_riichi:      bool
    :param tenpai_player_melds:       Tenpai player. List of meld dicts
    :param tenpai_player_discards:    Tenpai player. List of discard dicts
    :param second_player_melds:       Second player. List of meld dicts
    :param second_player_discards:    Second player. List of discard dicts
    :param third_player_melds:        Third player. List of meld dicts
    :param third_player_discards:     Third player. List of discard dicts

    :return: list of 0 and 1 values
    """
    tiles_unique = 34

    max_dora_in_hand = 8
    max_dora_on_the_table = 16 + 3
    winds_input_size = 8

    tenpai_player_discards_input = [0 for _ in range(tiles_unique)]
    tenpai_player_melds_input = [1 for _ in range(tiles_unique)]
    winds_input = [0 for _ in range(winds_input_size)]
    dora_in_player_open_melds_input = [0 for _ in range(max_dora_in_hand)]
    not_visible_dora_on_the_table_input = [0 for _ in range(max_dora_on_the_table)]

    for discard_dict in tenpai_player_discards:
        tile = discard_dict["tile"] // 4
        tenpai_player_discards_input[tile] = 1

    for meld in tenpai_player_melds:
        tiles = meld["tiles"]
        for tile in tiles:
            tile = tile // 4
            tenpai_player_melds_input[tile] = 1

    out_tiles_136 = []

    for tile_136 in player_closed_hand:
        out_tiles_136.append(tile_136)

    for tile_136 in dora_indicators:
        out_tiles_136.append(tile_136)

    discards = [
        player_discards,
        tenpai_player_discards,
        second_player_discards,
        third_player_discards,
    ]

    for discards_list in discards:
        for x in discards_list:
            # we will add this tile in melds loop
            if x["was_taken_for_meld"]:
                continue

            out_tiles_136.append(x["tile"])

    melds = [player_melds, tenpai_player_melds, second_player_melds, third_player_melds]

    for meld_list in melds:
        for x in meld_list:
            out_tiles_136.extend(x["tiles"])

    out_tiles = [0 for _ in range(tiles_unique)]
    for x in out_tiles_136:
        tile = x // 4

        out_tiles[tile] += 1
        assert out_tiles[tile] <= 4

    out_tiles_0 = [1 if x >= 1 else 0 for x in out_tiles]
    out_tiles_1 = [1 if x >= 2 else 0 for x in out_tiles]
    out_tiles_2 = [1 if x >= 3 else 0 for x in out_tiles]
    out_tiles_3 = [1 if x == 4 else 0 for x in out_tiles]

    if round_wind == EAST:
        winds_input[0] = 1
    elif round_wind == SOUTH:
        winds_input[1] = 1
    elif round_wind == WEST:
        winds_input[2] = 1
    elif round_wind == NORTH:
        winds_input[3] = 1

    if tenpai_player_wind == EAST:
        winds_input[4] = 1
    elif tenpai_player_wind == SOUTH:
        winds_input[5] = 1
    elif tenpai_player_wind == WEST:
        winds_input[6] = 1
    elif tenpai_player_wind == NORTH:
        winds_input[7] = 1

    number_of_dora_in_player_open_melds = 0
    player_melds = tenpai_player_melds
    for meld in player_melds:
        for tile in meld["tiles"]:
            number_of_dora_in_player_open_melds += plus_dora(tile, dora_indicators)
            if is_aka_dora(tile, True):
                number_of_dora_in_player_open_melds += 1

    if number_of_dora_in_player_open_melds > max_dora_in_hand:
        number_of_dora_in_player_open_melds = max_dora_in_hand

    for i in range(max_dora_in_hand):
        if i + 1 <= number_of_dora_in_player_open_melds:
            dora_in_player_open_melds_input[i] = 1

    visible_dora = 0
    for visible_tile in out_tiles:
        visible_dora += plus_dora(visible_tile, dora_indicators)
        if is_aka_dora(visible_tile, True):
            visible_dora += 1

    not_visible_dora = max_dora_on_the_table - visible_dora

    for i in range(max_dora_on_the_table):
        if i + 1 <= not_visible_dora:
            not_visible_dora_on_the_table_input[i] = 1

    return list(
        itertools.chain(
            winds_input,
            not_visible_dora_on_the_table_input,
            dora_in_player_open_melds_input,
            tenpai_player_discards_input,
            tenpai_player_melds_input,
            out_tiles_0,
            out_tiles_1,
            out_tiles_2,
            out_tiles_3,
        )
    )


class OpenHandCostProtocol(Protocol):
    tiles_unique = 34
    tiles_num = tiles_unique * 4

    input_size = 239
    output_size = 9

    hand_cost_mapping = {
        "1-30": 0,
        "1-40": 0,
        "1-50": 0,
        "2-25": 1,
        "2-30": 1,
        "2-40": 1,
        "2-50": 1,
        "3-25": 2,
        "3-30": 2,
        "3-40": 2,
        "3-50": 2,
        "3-60": 3,
        "4-25": 3,
        "4-30": 3,
        "4-40": 4,
        "4-50": 4,
        "5": 4,
        "6": 5,
        "7": 5,
        "8": 6,
        "9": 6,
        "10": 6,
        "11": 7,
        "12": 7,
        "13": 8,
    }

    def parse_new_data(self, raw_data):
        for index, row in raw_data:
            dora_indicators = [int(x) for x in str(row["dora_indicators"]).split(",")]
            player_hand = [int(x) for x in str(row["player_hand"]).split(",")]

            input_data = prepare_closed_hand_input(
                int(row["round_wind"]),
                dora_indicators,
                player_hand,
                self.prepare_melds(row["player_melds"]),
                self.prepare_discards(row["player_discards"]),
                int(row["tenpai_player_wind"]),
                row["tenpai_player_in_riichi"] == 1,
                self.prepare_melds(row["tenpai_player_melds"]),
                self.prepare_discards(row["tenpai_player_discards"]),
                self.prepare_melds(row["second_player_melds"]),
                self.prepare_discards(row["second_player_discards"]),
                self.prepare_melds(row["third_player_melds"]),
                self.prepare_discards(row["third_player_discards"]),
            )

            input_data = self.after_input_completed(row, input_data)

            if len(input_data) != self.input_size:
                print(
                    "Internal error: len(input_data) should be {}, but is {}".format(
                        self.input_size, len(input_data)
                    )
                )
                exit(1)

            self.input_data.append(input_data)

            tenpai_discards = self.prepare_discards(row["tenpai_player_discards"])
            tenpai_melds = self.prepare_melds(row["tenpai_player_melds"])

            # let's find maximum hand cost for now
            waiting_temp = [x for x in row["tenpai_player_waiting"].split(",")]
            waiting = None
            waiting_index = 0
            for x in waiting_temp:
                temp = x.split(";")

                if temp[2] == "None":
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
            tenpai_player_hand = [int(x) for x in row["tenpai_player_hand"].split(",")]
            verification_data = [
                tenpai_player_hand,
                tenpai_discards,
                tenpai_melds,
                waiting,
                [x // 4 for x in player_hand],
                dora_indicators,
            ]

            self.verification_data.append(verification_data)

    def after_input_completed(self, row, input_data):
        return input_data

    @staticmethod
    def create_hand_cost_key(han, fu):
        if fu >= 60 and han < 5:
            han += 1
            fu = 30

        if han >= 13:
            han = 13

        if han >= 5:
            key = str(han)
        else:
            key = "{}-{}".format(han, fu)

        return key
