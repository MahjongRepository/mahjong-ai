import itertools

from base.protocol import Protocol


class AgariRiichiCostProtocol(Protocol):
    input_size = 58
    output_size = 10

    CSV_HEADER = [
        "is_dealer",
        "riichi_called_on_step",
        "current_enemy_step",
        "wind_number",
        "scores",
        "is_tsumogiri_riichi",
        "is_oikake_riichi",
        "is_oikake_riichi_against_dealer_riichi_threat",
        "is_riichi_against_open_hand_threat",
        "number_of_kan_in_enemy_hand",
        "number_of_dora_in_enemy_kan_sets",
        "number_of_yakuhai_enemy_kan_sets",
        "number_of_other_player_kan_sets",
        "live_dora_tiles",
        "tile_plus_dora",
        "tile_category",
        "discards_before_riichi_34",
        "predicted_cost",
        "lobby",
        "log_id",
        "win_tile_34",
        "han",
        "fu",
        "original_cost",
    ]

    HAND_COST_CATEGORIES = {
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

    def parse_new_data(self, raw_data_list):
        for index, row in raw_data_list:
            input_data = self.prepare_input(row)
            assert self.input_size == len(
                input_data
            ), f"input_data len should be {self.input_size}, but it is {len(input_data)}"
            self.input_data.append(input_data)
            self.output_data.append(self.prepare_output(row))
            self.verification_data.append([row["original_cost"], row["han"], row["fu"], row["is_dealer"]])

    def prepare_output(self, row):
        category = AgariRiichiCostProtocol.HAND_COST_CATEGORIES.get(
            AgariRiichiCostProtocol.build_category_key(row["han"], row["fu"])
        )
        assert category is not None, row
        return category

    def prepare_input(self, row):
        step_input_size = 24
        max_dora_in_hand = 8

        riichi_called_on_step_input = [0 for _ in range(step_input_size)]
        riichi_called_on_step_input[row["riichi_called_on_step"]] = 1

        kan_sets_in_hand_input = self.fill_int_value(row["number_of_kan_in_enemy_hand"], 4)
        other_kan_sets_in_hand_input = self.fill_int_value(row["number_of_other_player_kan_sets"], 4)
        dora_in_hand_input = self.fill_int_value(row["number_of_dora_in_enemy_kan_sets"], max_dora_in_hand)
        live_dora_tiles_input = self.fill_int_value(row["live_dora_tiles"], max_dora_in_hand)
        tile_plus_dora_input = self.fill_int_value(row["tile_plus_dora"], 4)

        tile_category_input = [0 for _ in range(5)]
        if row["tile_category"] == "middle":
            tile_category_input[0] = 1
        if row["tile_category"] == "edge":
            tile_category_input[1] = 1
        if row["tile_category"] == "terminal":
            tile_category_input[2] = 1
        if row["tile_category"] == "honor":
            tile_category_input[3] = 1
        if row["tile_category"] == "valuable_honor":
            tile_category_input[4] = 1

        return list(
            itertools.chain(
                riichi_called_on_step_input,
                kan_sets_in_hand_input,
                other_kan_sets_in_hand_input,
                dora_in_hand_input,
                live_dora_tiles_input,
                tile_plus_dora_input,
                tile_category_input,
                [row["is_tsumogiri_riichi"] and 1 or 0],
            )
        )

    def fill_int_value(self, value, max_value):
        input_response = [0 for _ in range(max_value)]
        if value > max_value:
            value = max_value
        for i in range(value):
            input_response[i] = 1
        return input_response

    @staticmethod
    def build_category_key(han, fu):
        if fu > 50 and han <= 4:
            fu = 30
            han += 1

        if han > 13:
            han = 13

        if han >= 5:
            return str(han)
        else:
            return f"{han}-{fu}"
