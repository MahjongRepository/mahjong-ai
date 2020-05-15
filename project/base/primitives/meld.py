from mahjong.meld import Meld


class ParserMeld(Meld):
    def to_json(self):
        return {
            "type": self.type,
            "tiles": self.tiles,
            "opened": self.opened,
            "from_who": self.from_who,
        }
