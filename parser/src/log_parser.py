# -*- coding: utf-8 -*-
import logging
import re

from mahjong.agari import Agari
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.meld import Meld
from mahjong.shanten import Shanten

from src.primitives.table import Table

logger = logging.Logger('catch_all')


class LogParser:
    csv_exporter = None
    tenpai_player = None

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

        self.step = 0
        for hand in game:
            self.table = Table()

            self.who_called_meld = []
            log_id = None
            self.tenpai_player = None

            try:
                for tag in hand:
                    if self._is_log_id(tag):
                        log_id = self._get_attribute_content(tag, 'id')
                        self.table.log_id = log_id

                    if self._is_init_tag(tag):
                        seed = [int(x) for x in self._get_attribute_content(tag, 'seed').split(',')]
                        current_hand = seed[0]
                        dora_indicator = seed[5]
                        dealer_seat = int(self._get_attribute_content(tag, 'oya'))

                        self.table.init(dealer_seat, current_hand, dora_indicator, self.step)

                        self.table.get_player(0).init_hand(self._get_attribute_content(tag, 'hai0'))
                        self.table.get_player(1).init_hand(self._get_attribute_content(tag, 'hai1'))
                        self.table.get_player(2).init_hand(self._get_attribute_content(tag, 'hai2'))
                        self.table.get_player(3).init_hand(self._get_attribute_content(tag, 'hai3'))

                        self.step += 1

                        self.tenpai_player = None

                    if self._is_draw(tag):
                        tile = self._parse_tile(tag)
                        player_seat = self._get_player_seat(tag)
                        player = self.table.get_player(player_seat)

                        player.draw_tile(tile)

                    if self._is_meld_set(tag):
                        meld = self._parse_meld(tag)
                        player = self.table.get_player(meld.who)

                        # when we called chankan we need to remove pon set from hand
                        if meld.type == Meld.CHANKAN:
                            player.tiles.remove(meld.called_tile)
                            pon_set = [x for x in player.melds if x.tiles[0] == meld.tiles[0]][0]
                            player.melds.remove(pon_set)

                        player.add_meld(meld)

                        # if it was not kan/chankan let's draw a tile
                        if meld.type != Meld.CHANKAN and meld.type != Meld.KAN:
                            player.draw_tile(meld.called_tile)

                        # indication that tile was taken from discard
                        if meld.opened:
                            for meld_player in self.table.players:
                                if meld_player.discards and meld_player.discards[-1].tile == meld.called_tile:
                                    meld_player.discards[-1].was_given_for_meld = True

                        # for closed kan we had to remove tile from hand
                        if meld.type == Meld.KAN and not meld.opened:
                            # in riichi we will not have tile in hand
                            if meld.called_tile in player.tiles:
                                player.tiles.remove(meld.called_tile)

                        self.who_called_meld.append(meld.who)

                    if self._is_riichi(tag):
                        riichi_step = int(self._get_attribute_content(tag, 'step'))
                        who = int(self._get_attribute_content(tag, 'who'))
                        player = self.table.get_player(who)

                        if riichi_step == 1:
                            player.in_riichi = True

                        if riichi_step == 2:
                            player.discards[-1].after_riichi = True

                        if self._is_new_dora(tag):
                            dora = int(self._get_attribute_content(tag, 'hai'))
                            self.table.add_dora(dora)

            except Exception as e:
                logger.error(e, exc_info=True)
                print('Failed to process log: {}'.format(log_id))

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

    def _is_new_dora(self, tag):
        return tag and '<DORA' in tag
