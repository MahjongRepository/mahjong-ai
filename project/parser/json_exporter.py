# -*- coding: utf-8 -*-


class JsonExporter(object):

    @staticmethod
    def export_player(player):
        discards = []
        for discard in player.discards:
            discards.append({
                'tile': discard.tile,
                'after_meld': discard.after_meld,
                'is_tsumogiri': discard.is_tsumogiri,
            })

        melds = []
        for meld in player.melds:
            melds.append({
                'type': meld.type,
                'tiles': [x for x in meld.tiles],
                'opened': meld.opened,
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
