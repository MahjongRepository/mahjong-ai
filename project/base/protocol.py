class Protocol:
    tiles_unique = 34
    tiles_num = tiles_unique * 4

    input_size = None
    output_size = None

    def __init__(self):
        self.input_data = []
        self.output_data = []
        self.verification_data = []

    def prepare_discards(self, data):
        discards_temp = [x for x in data.split(',')]
        result = []
        for x in discards_temp:
            temp = x.split(';')
            result.append({
                'tile': int(temp[0]),
                'is_tsumogiri': int(temp[1]) == 1,
                'is_after_meld': int(temp[2]) == 1,
                'was_taken_for_meld': int(temp[4]) == 1,
            })
        return result

    def prepare_melds(self, data):
        melds = []
        melds_temp = [x for x in data.split(',') if x]
        for x in melds_temp:
            temp = x.split(';')
            tiles = [int(x) for x in temp[1].split('/')]
            melds.append({
                'tiles': tiles,
                'type': temp[0]
            })
        return melds
