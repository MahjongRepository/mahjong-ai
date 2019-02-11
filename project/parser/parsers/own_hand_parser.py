from parser.exporters.own_hand_exporter import OwnHandCSVExporter
from parser.parser import LogParser


class OwnHandParser(LogParser):

    def __init__(self):
        self.csv_exporter = OwnHandCSVExporter()

    def process_player_tenpai(self, player):
        self.tenpai_player = player
        self.tenpai_player.waiting = self._calculate_costs(player)

        self.export_player_on_tenpai(self.tenpai_player)

    def export_player_on_tenpai(self, tenpai_player):
        self.csv_records[tenpai_player.seat] = self.csv_exporter.export_player(self.tenpai_player)
