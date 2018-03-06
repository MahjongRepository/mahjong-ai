# -*- coding: utf-8 -*-
from mahjong.meld import Meld


class CSVExporter(object):

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
            tenpai_player_waiting.append('{};{}'.format(
                x['tile'],
                x['cost'] or 0,
            ))

        data = [
            table.log_id,
            table.round_wind,
            ','.join([str(x) for x in table.dora_indicators]),
            ','.join([str(x) for x in tenpai_player.closed_hand]),
            ','.join(tenpai_player_waiting),
            encode_discards(tenpai_player.discards),
            encode_melds(tenpai_player.melds),
            tenpai_player.player_wind,
            tenpai_player.discards[-1].after_riichi and 1 or 0,
            ','.join([str(x) for x in player.closed_hand]),
            encode_discards(player.discards),
            encode_melds(player.melds),
            encode_discards(second_player.discards),
            encode_melds(second_player.melds),
            encode_discards(third_player.discards),
            encode_melds(third_player.melds),
        ]

        return data


def encode_discards(player_discards):
    discards = []
    for x in player_discards:
        discards.append('{};{};{};{}'.format(
            x.tile,
            x.is_tsumogiri and 1 or 0,
            x.after_meld and 1 or 0,
            x.after_riichi and 1 or 0,
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
