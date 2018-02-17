# -*- coding: utf-8 -*-


class Discard(object):
    
    def __init__(self, tile, is_tsumogiri, after_meld, after_riichi, tenpai_after_discard):
        """
        :param tile: int. 36 tiles format
        :param is_tsumogiri: bool. Was tile discarded from hand or from wall
        :param after_meld: bool. Was tile discarded after called meld or not
        :param tenpai_after_discard: bool. Is player tenpai or not
        """
        self.tile = tile
        self.is_tsumogiri = is_tsumogiri
        self.after_meld = after_meld
        self.after_riichi = after_riichi
        self.tenpai_after_discard = tenpai_after_discard
