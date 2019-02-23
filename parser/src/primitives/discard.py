

class Discard:
    
    def __init__(self, tile, is_tsumogiri, after_meld, after_riichi, tenpai_after_discard):
        self.tile = tile
        self.is_tsumogiri = is_tsumogiri
        self.after_meld = after_meld
        self.after_riichi = after_riichi
        self.tenpai_after_discard = tenpai_after_discard

    def to_json(self):
        return {
            'tile': self.tile,
            'is_tsumogiri': self.is_tsumogiri,
            'after_meld': self.after_meld,
            'after_riichi': self.after_riichi,
            'tenpai_after_discard': self.tenpai_after_discard,
        }
