# -*- coding: utf-8 -*-


class CSVExporter(object):

    @staticmethod
    def header():
        return [
            'player_hand',
            'waiting'
        ]

    @staticmethod
    def export_player(player):
        data = [
            ','.join([str(x) for x in player.tiles]),
            ','.join([str(x['tile']) for x in player.waiting]),
        ]
        return data
