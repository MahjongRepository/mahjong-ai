from base.utils.utils import encode_discards, encode_melds


class CSVExporter:

    @staticmethod
    def header():
        return [
            'log_id',
            'round_wind',
            'dora_indicators',
            'tenpai_player_hand',
            'tenpai_player_waiting',
            'tenpai_player_discards',
            'tenpai_player_melds',
            'tenpai_player_wind',
            'tenpai_player_in_riichi',
            'player_hand',
            'player_discards',
            'player_melds',
            'second_player_discards',
            'second_player_melds',
            'third_player_discards',
            'third_player_melds',
        ]

    @staticmethod
    def export_player(tenpai_player, player):
        table = tenpai_player.table

        added_seats = [tenpai_player.seat, player.seat]
        another_players = []

        for x in table.players:
            if x.seat not in added_seats:
                another_players.append(x)
                added_seats.append(x.seat)

        second_player = another_players[0]
        third_player = another_players[1]

        tenpai_player_waiting = []
        for x in tenpai_player.waiting:
            tenpai_player_waiting.append('{};{};{};{}'.format(
                x['tile'],
                x['cost'],
                x['han'],
                x['fu'],
            ))

        assert len(tenpai_player_waiting) > 0

        data = [
            table.log_id,
            table.round_wind,
            ','.join([str(x) for x in table.dora_indicators]),
            ','.join([str(x) for x in tenpai_player.closed_hand]),
            ','.join(tenpai_player_waiting),
            encode_discards(tenpai_player.discards),
            encode_melds(tenpai_player.melds),
            tenpai_player.player_wind,
            tenpai_player.in_riichi and 1 or 0,
            ','.join([str(x) for x in player.closed_hand]),
            encode_discards(player.discards),
            encode_melds(player.melds),
            encode_discards(second_player.discards),
            encode_melds(second_player.melds),
            encode_discards(third_player.discards),
            encode_melds(third_player.melds),
        ]

        return data
