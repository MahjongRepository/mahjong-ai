# -*- coding: utf-8 -*-
from parser.player import Player

EAST = 27
SOUTH = 28
WEST = 29
NORTH = 30


class Table(object):

    def __init__(self):
        self.dora = []

        self.dealer_seat = None
        self.current_hand = None
        self.log_id = None

        self.players = []

    def init(self, dealer_seat, current_hand, dora_indicator):
        self.dora = [dora_indicator]

        self.dealer_seat = dealer_seat
        self.current_hand = current_hand

        self.players = [Player(self, x) for x in range(0, 4)]

    def get_player(self, player_seat):
        return self.players[player_seat]

    @property
    def round_wind(self):
        if self.current_hand < 4:
            return EAST
        elif 4 <= self.current_hand < 8:
            return SOUTH
        elif 8 <= self.current_hand < 12:
            return WEST
        else:
            return NORTH
