from betaori_open_hand.parser import BetaoriOpenHandParser
from hand_cost_open.exporter import OpenHandCostCSVExporter


class OpenHandCostParser(BetaoriOpenHandParser):

    def __init__(self):
        super(OpenHandCostParser, self).__init__()

        self.csv_exporter = OpenHandCostCSVExporter
