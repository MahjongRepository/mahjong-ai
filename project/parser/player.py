# -*- coding: utf-8 -*-


class Player(object):

    def __init__(self, table, seat):
        self.table = table

        self.tiles = []
        self.discards = []
        self.waiting = []
        self.melds = []
        self.cost = 0
        self.seat = seat

    def init_hand(self, tiles_string):
        tiles = [int(x) for x in tiles_string.split(',')]
        self.tiles = tiles

    def discard_tile(self, discard_obj):
        self.tiles.remove(discard_obj.tile)
        self.discards.append(discard_obj)

    def draw_tile(self, tile):
        self.tiles.append(tile)

    def add_meld(self, meld):
        self.melds.append(meld)

    def set_waiting(self, waiting):
        self.waiting = waiting
