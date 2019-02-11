from parser.exporters.betaori_exporter import BetaoriCSVExporter
from parser.parser import LogParser


class BetaoriParser(LogParser):

    def __init__(self):
        self.csv_exporter = BetaoriCSVExporter()

    def process_player_tenpai(self, player):
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

                self.export_player_on_tenpai(self.tenpai_player)

    def export_player_on_draw_tile(self, player_seat, player):
        if self.tenpai_player:
            key = '{}_{}'.format(self.step, player_seat)
            if key not in self.csv_records and self.tenpai_player.seat != player_seat:
                self.csv_records[key] = self.csv_exporter.export_player(self.tenpai_player, player)
