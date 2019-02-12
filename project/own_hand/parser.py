from base.parser import LogParser
from own_hand.exporter import OwnHandCSVExporter


class OwnHandParser(LogParser):

    def __init__(self):
        self.csv_exporter = OwnHandCSVExporter()

    def process_player_tenpai(self, player):
        player.waiting = self._calculate_costs(player)
        self.export_player_on_tenpai(player)

    def export_player_on_tenpai(self, tenpai_player):
        key = '{}_{}'.format(self.step, tenpai_player.seat)
        if key not in self.csv_records:
            self.csv_records[key] = self.csv_exporter.export_player(tenpai_player)
