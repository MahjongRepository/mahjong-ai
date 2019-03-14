import itertools

from base.protocol import Protocol


def prepare_betaori_input(
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

    # tenpai_player_discards_input_second = [0 for _ in range(tiles_unique)]
    tenpai_player_discards_input = [0 for _ in range(tiles_unique)]
    # tenpai_player_tsumogiri_input = [1 for _ in range(tiles_unique)]
    # tenpai_player_after_meld_input = [0 for _ in range(tiles_unique)]
    tenpai_player_melds_input = [0 for _ in range(tiles_unique)]
    # tenpai_player_discards_last_input = [0 for _ in range(tiles_unique)]
    # tenpai_player_discards_second_last_input = [0 for _ in range(tiles_unique)]

    for i, discard_dict in enumerate(tenpai_player_discards):
        tile = discard_dict['tile'] // 4
        tenpai_player_discards_input[tile] = 1
    #     # tenpai_player_discards_input[tile] = 1
    #
    #     if discard_dict['is_tsumogiri']:
    #         tenpai_player_tsumogiri_input[tile] = 0
    #     #
    #     if discard_dict['is_after_meld']:
    #         tenpai_player_after_meld_input[tile] = 1
    #
    for meld in tenpai_player_melds:
        tiles = meld['tiles']
        for tile in tiles:
            tile = tile // 4
            tenpai_player_melds_input[tile] = 1
    #
    # is_last = True
    # for x in reversed(tenpai_player_discards):
    #     tile = x['tile'] // 4
    #     is_tsumogiri = x['is_tsumogiri']
    #
    #     if is_last:
    #         if not is_tsumogiri:
    #             tenpai_player_discards_last_input[tile] = 1
    #             is_last = False
    #
    #         continue
    #     else:
    #         if not is_tsumogiri:
    #             tenpai_player_discards_second_last_input[tile] = 1
    #             break
    #
    #         continue

    out_tiles_136 = []

    for tile_136 in player_closed_hand:
        out_tiles_136.append(tile_136)

    for tile_136 in dora_indicators:
        out_tiles_136.append(tile_136)

    discards = [
        player_discards,
        tenpai_player_discards,
        second_player_discards,
        third_player_discards
    ]

    for discards_list in discards:
        for x in discards_list:
            # we will add this tile in melds loop
            if x['was_taken_for_meld']:
                continue

            out_tiles_136.append(x['tile'])

    melds = [
        player_melds,
        tenpai_player_melds,
        second_player_melds,
        third_player_melds
    ]

    for meld_list in melds:
        for x in meld_list:
            out_tiles_136.extend(x['tiles'])

    out_tiles = [0 for _ in range(tiles_unique)]
    for x in out_tiles_136:
        tile = x // 4

        out_tiles[tile] += 1
        assert out_tiles[tile] <= 4

    out_tiles_0 = [1 if x >= 1 else 0 for x in out_tiles]
    out_tiles_1 = [1 if x >= 2 else 0 for x in out_tiles]
    out_tiles_2 = [1 if x >= 3 else 0 for x in out_tiles]
    out_tiles_3 = [1 if x == 4 else 0 for x in out_tiles]

    return list(itertools.chain(
        tenpai_player_discards_input,
        tenpai_player_melds_input,
        out_tiles_0,
        out_tiles_1,
        out_tiles_2,
        out_tiles_3,
    ))


class BetaoriClosedHandProtocol(Protocol):
    input_size = 204
    output_size = Protocol.tiles_unique

    def parse_new_data(self, raw_data):
        for index, row in raw_data:
            dora_indicators = [int(x) for x in str(row['dora_indicators']).split(',')]
            player_hand = [int(x) for x in str(row['player_hand']).split(',')]

            input_data = prepare_betaori_input(
                int(row['round_wind']),
                dora_indicators,
                player_hand,
                self.prepare_melds(row['player_melds']),
                self.prepare_discards(row['player_discards']),
                int(row['tenpai_player_wind']),
                row['tenpai_player_in_riichi'] == 1,
                self.prepare_melds(row['tenpai_player_melds']),
                self.prepare_discards(row['tenpai_player_discards']),
                self.prepare_melds(row['second_player_melds']),
                self.prepare_discards(row['second_player_discards']),
                self.prepare_melds(row['third_player_melds']),
                self.prepare_discards(row['third_player_discards']),
            )

            if len(input_data) != self.input_size:
                print('Internal error: len(input_data) should be {}, but is {}'.format(
                    self.input_size,
                    len(input_data)
                ))
                exit(1)

            self.input_data.append(input_data)

            # Output reference - actual waits
            # For tiles that are not 100% safe and not actual waits,
            # we give value 0
            waiting = [0 for _ in range(self.tiles_num // 4)]

            tenpai_discards = self.prepare_discards(row['tenpai_player_discards'])
            tenpai_melds = self.prepare_melds(row['tenpai_player_melds'])

            for x in tenpai_discards:
                # Here we give hint to network during training: tiles from discard
                # give output "-1":
                waiting[x['tile'] // 4] = -1

            tenpai_player_waiting = [x for x in row['tenpai_player_waiting'].split(',')]
            for x in tenpai_player_waiting:
                temp = x.split(';')
                tile = int(temp[0])

                # if cost == 0 it mean that player can't win on this waiting
                cost = int(temp[1])
                if cost > 0:
                    waiting[tile // 4] = 1

            self.output_data.append(waiting)

            # Use it only for visual debugging!
            tenpai_player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]
            verification_data = [
                tenpai_player_hand,
                tenpai_discards,
                tenpai_melds,
                tenpai_player_waiting,
                [x // 4 for x in player_hand]
            ]

            self.verification_data.append(verification_data)
