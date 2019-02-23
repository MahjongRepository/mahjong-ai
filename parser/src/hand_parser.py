from src.log_parser import LogParser


class HandsParser(LogParser):

    def on_player_draw(self, player, table):
        hand = player.closed_hand
        assert 0 < len(hand) <= 14

        self.data_to_save.append({
            'discarded_tile': None,
            'player_seat': player.seat,
            'hand': hand,
            'discards': [x.to_json() for x in player.discards],
            'melds': [x.to_json() for x in player.melds],
        })

    def on_player_discard(self, player, table, discarded_tile):
        latest_data = self.data_to_save[-1]
        latest_data['discarded_tile'] = discarded_tile

    def after_tsumo(self, player):
        # when player win by self draw
        # we need to remove the previously added data from results
        # because there will be no discard after that
        del self.data_to_save[-1]
