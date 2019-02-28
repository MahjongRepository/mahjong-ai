from betaori_closed_hand.parser import BetaoriClosedHandParser


class BetaoriOpenHandParser(BetaoriClosedHandParser):

    def export_condition(self, player):
        # we want to collect only examples with open hands
        open_melds = [x.tiles for x in player.melds if x.opened]
        if not open_melds:
            return False

        return True
