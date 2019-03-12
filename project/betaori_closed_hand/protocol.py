import itertools

from base.protocol import Protocol


class BetaoriClosedHandProtocol(Protocol):
    input_size = Protocol.tiles_unique * 10
    output_size = Protocol.tiles_unique

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

            for x in self.prepare_discards(row['player_discards']):
                out_tiles[x[0] // 4] += 1

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
                tsumogiri,
                after_meld,
                melds,
                discards_last,
                discards_second_last,
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

            # Output reference - actual waits
            # For tiles that are not 100% safe and not actual waits,
            # we give value 0
            waiting = [0 for x in range(self.tiles_num // 4)]

            tenpai_discards = self.prepare_discards(row['tenpai_player_discards'])
            tenpai_melds = self.prepare_melds(row['tenpai_player_melds'])

            for x in tenpai_discards:
                # Here we give hint to network during training: tiles from discard
                # give output "-1":
                waiting[x[0] // 4] = -1

            waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
            for x in waiting_temp:
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
                waiting_temp,
                defending_hand
            ]

            self.verification_data.append(verification_data)
