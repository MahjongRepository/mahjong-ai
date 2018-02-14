# -*- coding: utf-8 -*-
import re


class LogParser(object):

    def get_game_rounds(self, log_content):
        """
        XML parser was really slow here,
        so I built simple parser to separate log content on tags (grouped by round)
        """
        tag_start = 0
        rounds = []
        tag = None
        current_rounds = []

        for x in range(0, len(log_content)):
            if log_content[x] == '>':
                tag = log_content[tag_start:x+1]
                tag_start = x + 1

            # not useful tags
            skip_tags = ['SHUFFLE', 'TAIKYOKU', 'mjloggm', 'GO', 'UN']
            if tag and any([x in tag for x in skip_tags]):
                tag = None

            # new round was started
            if tag and 'INIT' in tag and current_rounds:
                rounds.append(current_rounds)
                current_rounds = []

            # the end of the game
            if tag and 'owari' in tag:
                rounds.append(current_rounds)

            if tag:
                if 'INIT' in tag:
                    # we dont need seed information
                    # it appears in old logs format
                    find = re.compile(r'shuffle="[^"]*"')
                    tag = find.sub('', tag)

                # add processed tag to the round
                current_rounds.append(tag)
                tag = None

        return rounds
