# -*- coding: utf-8 -*-
import bz2
import sqlite3
from optparse import OptionParser

from parser.parser import LogParser


def main():
    parser = OptionParser()

    parser.add_option('-p', '--path',
                      type='string',
                      help='Path to .sqlite3 db with logs content')

    opts, _ = parser.parse_args()

    db_path = opts.path
    if not db_path:
        parser.error('Path to db is not given.')
        
    logs = load_logs(db_path, 1)
    parser = LogParser()
    for log_data in logs:
        game = parser.get_game_hands(log_data['log_content'])
        tenpai_players = parser.extract_tenpai_players(game)


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
