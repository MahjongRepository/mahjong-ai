class Protocol:
    tiles_unique = 34
    tiles_num = tiles_unique * 4

    input_size = None
    output_size = None

    def __init__(self):
        self.input_data = []
        self.output_data = []
        self.verification_data = []

    def process_discards(self, discards_data, melds_data, out_tiles):
        # For input we concatenate 5 rows of data for each player,
        # each row representing 136 tiles and their states:
        # First row - is discarded
        # Seconds row - tsumogiri flag
        # Third row - "after meld" flag
        # Fourth row - tile is present in open set
        # Fifth row - how long ago tile was discarded, 1 for first discard,
        #             and decreases by 0.025 for each following discard
        # NB: this should correspond to input_size variable!
        discards = [0 for _ in range(self.tiles_unique)]
        tsumogiri = [1 for _ in range(self.tiles_unique)]
        after_meld = [0 for _ in range(self.tiles_unique)]
        melds = [0 for _ in range(self.tiles_unique)]
        discards_last = [0 for _ in range(self.tiles_unique)]
        discards_second_last = [0 for _ in range(self.tiles_unique)]

        discards_temp = self.prepare_discards(discards_data)
        for x in discards_temp:
            tile = x[0] // 4
            is_tsumogiri = x[1]
            is_after_meld = x[2]
            # after_riichi = x[3]
            # taken_for_meld = x[4]

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

        melds_temp = self.prepare_melds(melds_data)
        for x in melds_temp:
            tiles = x[0]
            for tile in tiles:
                tile = tile // 4
                melds[tile] = 1
                out_tiles[tile] += 1

        return discards, tsumogiri, after_meld, melds, discards_last, discards_second_last, out_tiles

    def prepare_discards(self, data):
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
