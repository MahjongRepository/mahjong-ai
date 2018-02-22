# -*- coding: utf-8 -*-
from mahjong.meld import Meld


class CSVExporter(object):

    @staticmethod
    def header():
        return [
            'log_id',
            'player_hand',
            'waiting',
            'player_wind',
            'round_wind',
            'melds',
            'discards'
        ]

    @staticmethod
    def export_player(player):
        melds = []
        for meld in player.melds:
            meld_type = meld.type
            if meld_type == Meld.KAN and not meld.opened:
                meld_type = 'closed_kan'
            melds.append('{};{}'.format(meld_type, '/'.join([str(x) for x in meld.tiles])))

        discards = []
        for x in player.discards:
            discards.append('{};{};{}'.format(
                x.tile,
                x.is_tsumogiri and 1 or 0,
                x.after_meld and 1 or 0,
            ))

        waiting = []
        for x in player.waiting:
            waiting.append('{};{}'.format(
                x['tile'],
                x['cost'] or 0,
            ))

        data = [
            player.table.log_id,
            ','.join([str(x) for x in player.closed_hand]),
            ','.join(waiting),
            player.player_wind,
            player.table.round_wind,
            ','.join(melds),
            ','.join(discards)
        ]

        return data
