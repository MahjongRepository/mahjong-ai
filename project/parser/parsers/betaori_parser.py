from mahjong.tile import TilesConverter

from parser.discard import Discard
from parser.exporters.betaori_exporter import BetaoriCSVExporter
from parser.parser import LogParser


class BetaoriParser(LogParser):

    def __init__(self):
        self.csv_exporter = BetaoriCSVExporter()

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

        # for now let's work only with hand state in moment of first tenpai
        if not self.tenpai_player:
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
                    waiting = self._calculate_costs(player)
                    atodzuke_waiting = [x for x in waiting if x['cost'] is None]

                    # for now we don't need to add atodzuke waiting
                    if len(atodzuke_waiting) != len(waiting):
                        self.tenpai_player = player
                        self.tenpai_player.waiting = waiting

    def export_player_on_draw_tile(self, player_seat, player):
        if self.tenpai_player:
            key = '{}_{}'.format(self.step, player_seat)
            if key not in self.csv_records and self.tenpai_player.seat != player_seat:
                self.csv_records[key] = self.csv_exporter.export_player(self.tenpai_player, player)
