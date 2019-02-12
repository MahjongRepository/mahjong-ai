# -*- coding: utf-8 -*-
from base.utils import encode_melds


class OwnHandCSVExporter:

    @staticmethod
    def header():
        return [
            'log_id',
            'tenpai_player_hand',
            'tenpai_player_waiting',
            'tenpai_player_melds',
        ]

    @staticmethod
    def export_player(tenpai_player):
        table = tenpai_player.table

        tenpai_player_waiting = []
        for x in tenpai_player.waiting:
            tenpai_player_waiting.append('{};{}'.format(
                x['tile'],
                x['cost'] or 0,
            ))

        data = [
            table.log_id,
            ','.join([str(x) for x in tenpai_player.closed_hand]),
            ','.join(tenpai_player_waiting),
            encode_melds(tenpai_player.melds)
        ]

        return data

