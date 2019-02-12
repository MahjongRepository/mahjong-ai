# -*- coding: utf-8 -*-


class OwnHandCSVExporter:

    @staticmethod
    def header():
        return [
            'tenpai_player_hand',
            'tenpai_player_waiting',
        ]

    @staticmethod
    def export_player(tenpai_player):
        tenpai_player_waiting = []
        for x in tenpai_player.waiting:
            tenpai_player_waiting.append('{};{}'.format(
                x['tile'],
                x['cost'] or 0,
            ))

        data = [
            ','.join([str(x) for x in tenpai_player.closed_hand]),
            ','.join(tenpai_player_waiting),
        ]

        return data

