from mahjong.tile import TilesConverter

from base.discard import Discard
from base.parser import LogParser
from tenpai.exporter import TenpaiCSVExporter


class TenpaiParser(LogParser):

    def __init__(self):
        self.csv_exporter = TenpaiCSVExporter()

    def process_discard(self, tag):
        tile = self._parse_tile(tag)
        player_seat = self._get_player_seat(tag)
        player = self.table.get_player(player_seat)

        after_meld = player_seat in self.who_called_meld
        if after_meld:
            self.who_called_meld = []

        is_tsumogiri = tile == player.tiles[-1]

        after_riichi = self.tenpai_player and self.tenpai_player.in_riichi

        discard = Discard(tile, is_tsumogiri, after_meld, after_riichi, False)
        player.discard_tile(discard)

        key = '{}_{}'.format(self.step, player.seat)
        if key not in self.csv_records:
            tiles_34 = TilesConverter.to_34_array(player.tiles)
            melds_34 = player.melds_34
            if self.shanten.calculate_shanten(tiles_34, melds_34) == 0:
                waiting = self._get_waiting(self.table.get_player(player_seat))
                player.set_waiting(waiting)

                has_furiten = False
                for waiting_34 in player.waiting:
                    discards_34 = [x.tile // 4 for x in player.discards]

                    if waiting_34 in discards_34:
                        has_furiten = True

                if not has_furiten:
                    costs = self._calculate_costs(player)
                    atodzuke = len([x for x in costs if x['cost'] is None]) > 0

                    yaku_id = []
                    dora_number = 0
                    for x in costs:
                        for yaku in x['yaku']:
                            yaku_id.append(str(yaku.yaku_id))
                            if yaku.yaku_id == 52:
                                dora_number += yaku.han_open
                            if yaku.yaku_id == 54:
                                dora_number += yaku.han_open
                    yaku_id = list(set(yaku_id))

                    if yaku_id:
                        hand_cost = max([x['cost'] or 0 for x in costs])
                        self.csv_records[key] = self.csv_exporter.export_player(player, yaku_id, hand_cost, atodzuke, dora_number)
