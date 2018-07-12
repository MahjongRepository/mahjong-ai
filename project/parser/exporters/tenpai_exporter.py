# -*- coding: utf-8 -*-
from mahjong.meld import Meld


class TenpaiCSVExporter(object):

    @staticmethod
    def header():
        return [
            'log_id',
            'round_wind',
            'player_wind',
            'dora_indicators',
            'discards',
            'melds',
        ]

    @staticmethod
    def export_player(tenpai_player):
        table = tenpai_player.table

        data = [
            table.log_id,
            table.round_wind,
            tenpai_player.player_wind,
            ','.join([str(x) for x in table.dora_indicators]),
            encode_discards(tenpai_player.discards),
            encode_melds(tenpai_player.melds),
        ]

        return data


def encode_discards(player_discards):
    discards = []
    for x in player_discards:
        discards.append('{};{};{};{};{}'.format(
            x.tile,
            x.is_tsumogiri and 1 or 0,
            x.after_meld and 1 or 0,
            x.after_riichi and 1 or 0,
            x.was_given_for_meld and 1 or 0,
        ))
    return ','.join(discards)


def encode_melds(player_melds):
    melds = []
    for meld in player_melds:
        meld_type = meld.type
        if meld_type == Meld.KAN and not meld.opened:
            meld_type = 'closed_kan'
        melds.append('{};{}'.format(meld_type, '/'.join([str(x) for x in meld.tiles])))
    return ','.join(melds)
