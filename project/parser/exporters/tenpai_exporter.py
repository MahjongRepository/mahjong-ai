# -*- coding: utf-8 -*-

class TenpaiCSVExporter(object):

    @staticmethod
    def header():
        return [
            'player_wind',
            'step',
            'count_melds',
            'yaku_list',
            'riichi',
            'hand_cost',
            'atodzuke',
            'count_dora'
        ]

    @staticmethod
    def export_player(tenpai_player, yaku_id, cost, atodzuke, dora_number):
        table = tenpai_player.table

        # 54, 52 are dora
        if '54' in yaku_id:
            yaku_id.remove('54')
        if '52' in yaku_id:
            yaku_id.remove('52')

        data = [
            tenpai_player.player_wind,
            len(tenpai_player.discards),
            len(tenpai_player.melds),
            ','.join(yaku_id),
            tenpai_player.in_riichi and 1 or 0,
            cost,
            atodzuke and 1 or 0,
            dora_number
        ]

        return data
