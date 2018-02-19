# -*- coding: utf-8 -*-


class JsonExporter(object):

    @staticmethod
    def export_player(player):
        """
        Let's export tiles in 34 tile format.
        It will allow to build more clear predictions.
        """

        discards = []
        for discard in player.discards:
            discards.append({
                'tile': discard.tile,
                'after_meld': discard.after_meld,
            })

        melds = []
        for meld in player.melds:
            melds.append({
                'type': meld.type,
                'tiles': [x for x in meld.tiles]
            })

        data = {
            'after_riichi': player.discards[-1].after_riichi,
            'log_id': player.table.log_id,
            'player_seat': player.seat,
            'step': player.table.step,
            'round_wind': player.table.round_wind,
            'player_wind': player.player_wind,
            'player_hand': sorted([x for x in player.closed_hand]),
            'discards': discards,
            'dora_indicators': player.table.dora_indicators,
            'melds': melds,
            'waiting': player.waiting,
        }

        return data
