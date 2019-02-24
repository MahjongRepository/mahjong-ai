

class Discard:
    
    def __init__(self, tile, is_tsumogiri, after_meld, after_riichi):
        self.tile = tile
        self.is_tsumogiri = is_tsumogiri
        self.after_meld = after_meld
        self.after_riichi = after_riichi

        self.tenpai_after_discard = False
        self.was_given_for_meld = False
