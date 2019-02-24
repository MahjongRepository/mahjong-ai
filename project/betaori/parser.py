from base.log_parser import LogParser
from betaori.exporter import BetaoriCSVExporter


class BetaoriParser(LogParser):

    def __init__(self):
        super(BetaoriParser, self).__init__()

        self.csv_exporter = BetaoriCSVExporter()

    def on_player_tenpai(self, player, table):
        waiting = self.get_player_waiting(player)

        has_furiten = False
        for waiting_34 in waiting:
            discards_34 = [x.tile // 4 for x in player.discards]

            if waiting_34 in discards_34:
                has_furiten = True

        # we don't want to analyze furiten waiting for now
        if has_furiten:
            return False

        waiting = self.calculate_waiting_costs(player, waiting)
        atodzuke_waiting = [x for x in waiting if not x['cost']]

        # we don't want to analyze atodzuke waiting for now
        if len(atodzuke_waiting) == len(waiting):
            return False

        player.waiting = waiting
        player.in_tempai = True

    def on_player_draw(self, player, table):
        tenpai_players = [x for x in table.players if x.in_tempai]

        for tenpai_player in tenpai_players:
            if tenpai_player.seat != player.seat:
                self.data_to_save.append(self.csv_exporter.export_player(tenpai_player, player))
