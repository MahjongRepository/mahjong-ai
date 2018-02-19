# -*- coding: utf-8 -*-
import copy

from mahjong.constants import EAST, NORTH, WEST, SOUTH


class Player(object):

    def __init__(self, table, seat, dealer_seat):
        self.table = table

        self.tiles = []
        self.discards = []
        self.waiting = []
        self.melds = []
        self.cost = 0
        self.seat = seat
        self.dealer_seat = dealer_seat

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

    @property
    def player_wind(self):
        seats = [0, 1, 2, 3]
        position = seats[self.dealer_seat - self.seat]
        if position == 0:
            return EAST
        elif position == 1:
            return NORTH
        elif position == 2:
            return WEST
        else:
            return SOUTH

    @property
    def melds_34(self):
        """
        Array of array with 34 tiles indices
        """
        melds = [x.tiles for x in self.melds if x.opened]
        melds = copy.deepcopy(melds)
        results = []
        for meld in melds:
            results.append([meld[0] // 4, meld[1] // 4, meld[2] // 4])
        return results

    @property
    def closed_hand(self):
        tiles = self.tiles[:]
        return [item for item in tiles if item not in self.meld_tiles]

    @property
    def meld_tiles(self):
        """
        Array of 136 tiles format
        :return:
        """
        result = []
        for meld in self.melds:
            result.extend(meld.tiles)
        return result
