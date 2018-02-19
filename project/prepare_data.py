# -*- coding: utf-8 -*-
import bz2
import json
import sqlite3
from optparse import OptionParser

import os

from parser.exporter import JsonExporter
from parser.parser import LogParser

data_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'visual', 'data')
if not os.path.exists(data_directory):
    os.mkdir(data_directory)


def main():
    parser = OptionParser()

    parser.add_option('-p', '--path',
                      type='string',
                      help='Path to .sqlite3 db with logs content')

    opts, _ = parser.parse_args()

    db_path = opts.path
    if not db_path:
        parser.error('Path to db is not given.')

    logs = load_logs(db_path, 10)
    parser = LogParser()
    for log_data in logs:
        game = parser.get_game_hands(log_data['log_content'], log_data['log_id'])

        tenpai_players = parser.extract_tenpai_players(game)
        save_data(tenpai_players)


def save_data(tenpai_players):
    for player in tenpai_players:
        file_name = '{}_{}_{}.json'.format(
            player.table.log_id,
            player.seat,
            player.table.step,
        )
        print('http://127.0.0.1:8010/?hand={}'.format(file_name))

        file_path = os.path.join(data_directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path, 'w') as f:
            f.write(json.dumps(JsonExporter.export_player(player)))


def load_logs(db_path, limit=10, offset=0):
    """
    Load logs from db and decompress logs content.
    How to download games content you can learn there: https://github.com/MahjongRepository/phoenix-logs
    """
    connection = sqlite3.connect(db_path)

    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT log_id, log_content FROM logs where is_hirosima = 0 LIMIT ? OFFSET ?;', 
                       [limit, offset])
        data = cursor.fetchall()
        
    results = []
    for x in data:
        results.append({
            'log_id': x[0], 
            'log_content': bz2.decompress(x[1]).decode('utf-8')
        })
        
    return results


if __name__ == '__main__':
    main()
