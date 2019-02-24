import logging
import re

from mahjong.agari import Agari
from mahjong.constants import AKA_DORA_LIST
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter

from base.primitives.discard import Discard
from base.primitives.meld import ParserMeld
from base.primitives.table import Table

logger = logging.Logger('catch_all')


class LogParser:
    data_to_save = None

    def __init__(self):
        self.shanten = Shanten()
        self.agari = Agari()
        self.finished_hand = HandCalculator()

        self.data_to_save = []

    def on_player_draw(self, player, table):
        pass

    def on_player_discard(self, player, table, discarded_tile):
        pass

    def on_player_tenpai(self, player, table):
        pass

    def get_game_rounds(self, log_content, log_id):
        """
        XML parser was really slow here,
        so I built simple parser to separate log content on tags (grouped by rounds)
        """
        tag_start = 0
        rounds = []
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
            if self.is_init_tag(tag) and current_tags:
                rounds.append(current_tags)
                current_tags = []

            # the end of the game
            if tag and 'owari' in tag:
                rounds.append(current_tags)

            if tag:
                if self.is_init_tag(tag):
                    # we dont need seed information
                    # it appears in old logs format
                    find = re.compile(r'shuffle="[^"]*"')
                    tag = find.sub('', tag)

                    current_tags.append('<LOG_ID id="{}" />'.format(log_id))

                # add processed tag to the hand
                current_tags.append(tag)
                tag = None

        return rounds

    def parse_game_rounds(self, game):
        self.data_to_save = []
        step = 0
        for round_item in game:
            table = Table()

            log_id = None
            who_called_meld_on_this_step = None

            try:
                for tag in round_item:
                    if self.is_log_id(tag):
                        log_id = self.get_attribute_content(tag, 'id')
                        table.log_id = log_id

                    if self.is_init_tag(tag):
                        seed = [int(x) for x in self.get_attribute_content(tag, 'seed').split(',')]
                        current_hand = seed[0]
                        dora_indicator = seed[5]
                        dealer_seat = int(self.get_attribute_content(tag, 'oya'))

                        table.init(dealer_seat, current_hand, dora_indicator, step)

                        table.get_player(0).init_hand(self.get_attribute_content(tag, 'hai0'))
                        table.get_player(1).init_hand(self.get_attribute_content(tag, 'hai1'))
                        table.get_player(2).init_hand(self.get_attribute_content(tag, 'hai2'))
                        table.get_player(3).init_hand(self.get_attribute_content(tag, 'hai3'))

                        step += 1

                    if self.is_draw(tag):
                        tile = self.parse_tile(tag)
                        player_seat = self.get_player_seat(tag)
                        player = table.get_player(player_seat)

                        player.draw_tile(tile)

                        self.on_player_draw(player, table)

                    if self.is_discard(tag):
                        tile = self.parse_tile(tag)
                        player_seat = self.get_player_seat(tag)
                        player = table.get_player(player_seat)

                        is_tsumogiri = tile == player.tiles[-1]
                        after_meld = player_seat == who_called_meld_on_this_step

                        discard = Discard(tile, is_tsumogiri, after_meld, False)
                        player.discard_tile(discard)

                        tenpai_after_discard = False
                        tiles_34 = TilesConverter.to_34_array(player.tiles)
                        melds_34 = player.melds_34
                        if self.shanten.calculate_shanten(tiles_34, melds_34) == 0:
                            tenpai_after_discard = True

                            self.on_player_tenpai(player, table)
                        else:
                            player.in_tempai = False

                        player.discards[-1].tenpai_after_discard = tenpai_after_discard
                        who_called_meld_on_this_step = None
                        self.on_player_discard(player, table, tile)

                    if self.is_meld_set(tag):
                        meld = self.parse_meld(tag)
                        player = table.get_player(meld.who)

                        # when we called chankan we need to remove pon set from hand
                        if meld.type == ParserMeld.CHANKAN:
                            player.tiles.remove(meld.called_tile)
                            pon_set = [x for x in player.melds if x.tiles[0] == meld.tiles[0]][0]
                            player.melds.remove(pon_set)

                        player.add_meld(meld)

                        # if it was not kan/chankan let's draw a tile
                        if meld.type != ParserMeld.CHANKAN and meld.type != ParserMeld.KAN:
                            player.draw_tile(meld.called_tile)

                        # indication that tile was taken from discard
                        if meld.opened:
                            for meld_player in table.players:
                                if meld_player.discards and meld_player.discards[-1].tile == meld.called_tile:
                                    meld_player.discards[-1].was_given_for_meld = True

                        # for closed kan we had to remove tile from hand
                        if meld.type == ParserMeld.KAN and not meld.opened:
                            # in riichi we will not have tile in hand
                            if meld.called_tile in player.tiles:
                                player.tiles.remove(meld.called_tile)

                        who_called_meld_on_this_step = meld.who

                    if self.is_riichi(tag):
                        riichi_step = int(self.get_attribute_content(tag, 'step'))
                        who = int(self.get_attribute_content(tag, 'who'))
                        player = table.get_player(who)

                        if riichi_step == 1:
                            player.in_riichi = True

                        if riichi_step == 2:
                            player.discards[-1].after_riichi = True

                    if self.is_new_dora(tag):
                        dora = int(self.get_attribute_content(tag, 'hai'))
                        table.add_dora(dora)

            except Exception as e:
                logger.error('Failed to process log: {}'.format(log_id))
                logger.error(e, exc_info=True)

        return self.data_to_save

    def get_player_waiting(self, player):
        tiles = player.closed_hand
        if len(tiles) == 1:
            return [tiles[0] // 4]

        tiles_34 = TilesConverter.to_34_array(tiles)

        waiting = []
        for j in range(0, 34):
            # we already have 4 tiles in hand
            # and we can't wait on 5th
            if tiles_34[j] == 4:
                continue

            tiles_34[j] += 1
            if self.agari.is_agari(tiles_34):
                waiting.append(j)
            tiles_34[j] -= 1

        return waiting

    def calculate_waiting_costs(self, player, player_waiting):
        waiting = []
        for tile in player_waiting:
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

            result = self.finished_hand.estimate_hand_value(
                tiles,
                win_tile,
                player.melds,
                player.table.dora_indicators,
                config
            )

            if result.error:
                waiting.append({
                    'tile': win_tile,
                    'han': None,
                    'fu': None,
                    'cost': 0,
                    'yaku': []
                })
            else:
                waiting.append({
                    'tile': win_tile,
                    'han': result.han,
                    'fu': result.fu,
                    'cost': result.cost['main'],
                    'yaku': [{'id': x.yaku_id, 'name': x.name} for x in result.yaku]
                })

        return waiting

    def get_attribute_content(self, tag, attribute_name):
        result = re.findall(r'{}="([^"]*)"'.format(attribute_name), tag)
        return result and result[0] or None

    def is_discard(self, tag):
        skip_tags = ['<GO', '<FURITEN', '<DORA']
        if any([x in tag for x in skip_tags]):
            return False

        match_discard = re.match(r"^<[defgDEFG]+\d*", tag)
        if match_discard:
            return True

        return False

    def is_draw(self, tag):
        match_discard = re.match(r"^<[tuvwTUVW]+\d*", tag)
        if match_discard:
            return True

        return False

    def parse_tile(self, message):
        result = re.match(r'^<[defgtuvwDEFGTUVW]+\d*', message).group()
        return int(result[2:])

    def get_player_seat(self, tag):
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

    def parse_meld(self, tag):
        who = int(self.get_attribute_content(tag, 'who'))
        data = int(self.get_attribute_content(tag, 'm'))

        meld = ParserMeld()
        meld.who = who
        meld.from_who = data & 0x3

        if data & 0x4:
            self.parse_chi(data, meld)
        elif data & 0x18:
            self.parse_pon(data, meld)
        elif data & 0x20:
            # nuki
            pass
        else:
            self.parse_kan(data, meld)

        return meld

    def parse_chi(self, data, meld):
        meld.type = ParserMeld.CHI
        t0, t1, t2 = (data >> 3) & 0x3, (data >> 5) & 0x3, (data >> 7) & 0x3
        base_and_called = data >> 10
        base = base_and_called // 3
        called = base_and_called % 3
        base = (base // 7) * 9 + base % 7
        meld.tiles = [t0 + 4 * (base + 0), t1 + 4 * (base + 1), t2 + 4 * (base + 2)]
        meld.called_tile = meld.tiles[called]

    def parse_pon(self, data, meld):
        t4 = (data >> 5) & 0x3
        t0, t1, t2 = ((1, 2, 3), (0, 2, 3), (0, 1, 3), (0, 1, 2))[t4]
        base_and_called = data >> 9
        base = base_and_called // 3
        called = base_and_called % 3
        if data & 0x8:
            meld.type = ParserMeld.PON
            meld.tiles = [t0 + 4 * base, t1 + 4 * base, t2 + 4 * base]
            meld.called_tile = meld.tiles[called]
        else:
            meld.type = ParserMeld.CHANKAN
            meld.tiles = [t0 + 4 * base, t1 + 4 * base, t2 + 4 * base, t4 + 4 * base]
            meld.called_tile = meld.tiles[3]

    def parse_kan(self, data, meld):
        base_and_called = data >> 8
        base = base_and_called // 4
        meld.type = ParserMeld.KAN
        meld.tiles = [4 * base, 1 + 4 * base, 2 + 4 * base, 3 + 4 * base]
        called = base_and_called % 4
        meld.called_tile = meld.tiles[called]
        # to mark closed\opened kans
        meld.opened = meld.who != meld.from_who

    def is_init_tag(self, tag):
        return tag and 'INIT' in tag

    def is_redraw_tag(self, tag):
        return tag and 'RYUUKYOKU' in tag

    def is_agari_tag(self, tag):
        return tag and 'AGARI' in tag

    def is_log_id(self, tag):
        return tag and 'LOG_ID' in tag

    def is_meld_set(self, tag):
        return tag and '<N who=' in tag

    def is_riichi(self, tag):
        return tag and 'REACH ' in tag

    def is_new_dora(self, tag):
        return tag and '<DORA' in tag
