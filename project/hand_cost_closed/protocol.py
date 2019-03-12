from hand_cost_open.protocol import OpenHandCostProtocol


class ClosedHandCostProtocol(OpenHandCostProtocol):
    input_size = 240

    def after_input_completed(self, row, input_data):
        # additional input for closed hand
        input_data.append(int(row['tenpai_player_in_riichi']))
        return input_data
