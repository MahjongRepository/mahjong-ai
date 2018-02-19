# -*- coding: utf-8 -*-
import copy
import re

from mahjong.agari import Agari
from mahjong.constants import AKA_DORA_LIST
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.meld import Meld
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter

from parser.discard import Discard
from parser.table import Table


class LogParser(object):

    def get_game_hands(self, log_content, log_id):
        """
        XML parser was really slow here,
        so I built simple parser to separate log content on tags (grouped by hands)
        """
        tag_start = 0
        hands = []
        tag = None

        current_tags = []

        for x in range(0, len(log_content)):
            if log_content[x] == '>':
                tag = log_content[tag_start:x+1]
                tag_start = x + 1

            # not useful tags
            skip_tags = ['SHUFFLE', 'TAIKYOKU', 'mjloggm', 'GO', 'UN']
            if tag and any([x in tag for x in skip_tags]):
                tag = None

            # new hand was started
            if self._is_init_tag(tag) and current_tags:
                hands.append(current_tags)
                current_tags = []

            # the end of the game
            if tag and 'owari' in tag:
                hands.append(current_tags)

            if tag:
                if self._is_init_tag(tag):
                    # we dont need seed information
                    # it appears in old logs format
                    find = re.compile(r'shuffle="[^"]*"')
                    tag = find.sub('', tag)

                    current_tags.append('<LOG_ID id="{}" />'.format(log_id))

                # add processed tag to the hand
                current_tags.append(tag)
                tag = None

        return hands

    def extract_tenpai_players(self, game):
        """
        In this method we will emulate played hands
        and will select hands with tenpai for future analysis
        """

        self.shanten = Shanten()
        self.agari = Agari()
        self.finished_hand = HandCalculator()

        tenpai_players = []

        step = 0
        for hand in game:
            table = Table()

            added_players = {}
            called_meld = []

            for tag in hand:
                if self._is_log_id(tag):
                    table.log_id = self._get_attribute_content(tag, 'id')

                if self._is_init_tag(tag):
                    seed = [int(x) for x in self._get_attribute_content(tag, 'seed').split(',')]
                    current_hand = seed[0]
                    dora_indicator = seed[5]
                    dealer_seat = int(self._get_attribute_content(tag, 'oya'))

                    table.init(dealer_seat, current_hand, dora_indicator, step)

                    table.get_player(0).init_hand(self._get_attribute_content(tag, 'hai0'))
                    table.get_player(1).init_hand(self._get_attribute_content(tag, 'hai1'))
                    table.get_player(2).init_hand(self._get_attribute_content(tag, 'hai2'))
                    table.get_player(3).init_hand(self._get_attribute_content(tag, 'hai3'))

                    step += 1

                if self._is_discard(tag):
                    tile = self._parse_tile(tag)
                    player_seat = self._get_player_seat(tag)
                    player = table.get_player(player_seat)

                    after_meld = player_seat in called_meld
                    if after_meld:
                        called_meld = []

                    is_tsumogiri = tile == player.tiles[-1]

                    discard = Discard(tile, is_tsumogiri, after_meld, False, False)
                    player.discard_tile(discard)

                    # for now let's work only with hand state in moment of first tenpai
                    if player_seat not in added_players:
                        tiles_34 = TilesConverter.to_34_array(player.tiles)
                        melds_34 = player.melds_34
                        if self.shanten.calculate_shanten(tiles_34, melds_34) == 0:
                            player.set_waiting(self._get_waiting(table.get_player(player_seat)))

                            added_players[player_seat] = copy.deepcopy(player)

                if self._is_draw(tag):
                    tile = self._parse_tile(tag)
                    player_seat = self._get_player_seat(tag)

                    table.get_player(player_seat).draw_tile(tile)

                if self._is_meld_set(tag):
                    meld = self._parse_meld(tag)
                    table.get_player(meld.who).add_meld(meld)
                    table.get_player(meld.who).draw_tile(meld.called_tile)

                    called_meld.append(meld.who)

                if self._is_riichi(tag):
                    riichi_step = int(self._get_attribute_content(tag, 'step'))
                    who = int(self._get_attribute_content(tag, 'who'))
                    if riichi_step == 2:
                        added_players[who].discards[-1].after_riichi = True

            tenpai_players.extend([x[1] for x in added_players.items()])

        for player in tenpai_players:
            player.waiting = self._calculate_costs(player)

        return tenpai_players

    def _get_attribute_content(self, tag, attribute_name):
        result = re.findall(r'{}="([^"]*)"'.format(attribute_name), tag)
        return result and result[0] or None

    def _is_discard(self, tag):
        skip_tags = ['<GO', '<FURITEN', '<DORA']
        if any([x in tag for x in skip_tags]):
            return False

        match_discard = re.match(r"^<[defgDEFG]+\d*", tag)
        if match_discard:
            return True

        return False

    def _is_draw(self, tag):
        match_discard = re.match(r"^<[tuvwTUVW]+\d*", tag)
        if match_discard:
            return True

        return False

    def _parse_tile(self, message):
        result = re.match(r'^<[defgtuvwDEFGTUVW]+\d*', message).group()
        return int(result[2:])

    def _get_player_seat(self, tag):
        player_sign = tag.lower()[1]
        if player_sign == 'd' or player_sign == 't':
            player_seat = 0
        elif player_sign == 'e' or player_sign == 'u':
            player_seat = 1
        elif player_sign == 'f' or player_sign == 'v':
            player_seat = 2
        else:
            player_seat = 3

        return player_seat

    def _parse_meld(self, tag):
        who = int(self._get_attribute_content(tag, 'who'))
        data = int(self._get_attribute_content(tag, 'm'))

        meld = Meld()
        meld.who = who
        meld.from_who = data & 0x3

        if data & 0x4:
            self._parse_chi(data, meld)
        elif data & 0x18:
            self._parse_pon(data, meld)
        elif data & 0x20:
            # nuki
            pass
        else:
            self._parse_kan(data, meld)

        return meld

    def _parse_chi(self, data, meld):
        meld.type = Meld.CHI
        t0, t1, t2 = (data >> 3) & 0x3, (data >> 5) & 0x3, (data >> 7) & 0x3
        base_and_called = data >> 10
        base = base_and_called // 3
        called = base_and_called % 3
        base = (base // 7) * 9 + base % 7
        meld.tiles = [t0 + 4 * (base + 0), t1 + 4 * (base + 1), t2 + 4 * (base + 2)]
        meld.called_tile = meld.tiles[called]

    def _parse_pon(self, data, meld):
        t4 = (data >> 5) & 0x3
        t0, t1, t2 = ((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2))[t4]
        base_and_called = data >> 9
        base = base_and_called // 3
        called = base_and_called % 3
        if data & 0x8:
            meld.type = Meld.PON
            meld.tiles = [t0 + 4 * base, t1 + 4 * base, t2 + 4 * base]
            meld.called_tile = meld.tiles[called]
        else:
            meld.type = Meld.CHANKAN
            meld.tiles = [t0 + 4 * base, t1 + 4 * base, t2 + 4 * base, t4 + 4 * base]
            meld.called_tile = meld.tiles[3]

    def _parse_kan(self, data, meld):
        base_and_called = data >> 8
        base = base_and_called // 4
        meld.type = Meld.KAN
        meld.tiles = [4 * base, 1 + 4 * base, 2 + 4 * base, 3 + 4 * base]
        called = base_and_called % 4
        meld.called_tile = meld.tiles[called]
        # to mark closed\opened kans
        meld.opened = meld.who != meld.from_who

    def _is_init_tag(self, tag):
        return tag and 'INIT' in tag

    def _is_redraw_tag(self, tag):
        return tag and 'RYUUKYOKU' in tag

    def _is_agari_tag(self, tag):
        return tag and 'AGARI' in tag

    def _is_log_id(self, tag):
        return tag and 'LOG_ID' in tag

    def _is_meld_set(self, tag):
        return tag and '<N who=' in tag

    def _is_riichi(self, tag):
        return tag and 'REACH ' in tag

    def _get_waiting(self, player):
        tiles = player.closed_hand
        if len(tiles) == 1:
            return tiles[0] // 4

        tiles_34 = TilesConverter.to_34_array(tiles)

        waiting = []
        for j in range(0, 34):
            tiles_34[j] += 1
            if self.agari.is_agari(tiles_34):
                waiting.append(j)
            tiles_34[j] -= 1

        return waiting

    def _calculate_costs(self, player):
        waiting = []
        for tile in player.waiting:
            config = HandConfig(
                is_riichi=player.discards[-1].after_riichi,
                player_wind=player.player_wind,
                round_wind=player.table.round_wind,
                has_aka_dora=True,
                has_open_tanyao=True
            )

            win_tile = tile * 4
            # we don't need to think, that our waiting is aka dora
            if win_tile in AKA_DORA_LIST:
                win_tile += 1

            tiles = player.tiles + [win_tile]

            result = self.finished_hand.estimate_hand_value(tiles,
                                                            win_tile,
                                                            player.melds,
                                                            player.table.dora_indicators,
                                                            config)

            if result.error:
                waiting.append({
                    'tile': win_tile,
                    'han': None,
                    'fu': None,
                    'cost': None,
                })
            else:
                waiting.append({
                    'tile': win_tile,
                    'han': result.han,
                    'fu': result.fu,
                    'cost': result.cost['main'],
                })

        return waiting
