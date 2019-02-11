# -*- coding: utf-8 -*-
import bz2
import csv
import datetime
import os
import sqlite3
from optparse import OptionParser

from parser.parsers.betaori_parser import BetaoriParser
from parser.parsers.own_hand_parser import OwnHandParser
from parser.parsers.tenpai_parser import TenpaiParser


def main():
    parser = OptionParser()

    parser.add_option('-d', '--data',
                      type='string',
                      help='Path to .sqlite3 db with logs content')

    parser.add_option('-f', '--file-csv',
                      type='string',
                      help='Path where to save output CSV')

    parser.add_option('-l', '--limit',
                      type='string',
                      help='For debugging',
                      default='unlimited')

    parser.add_option('-p', '--protocol',
                      type='string',
                      help='hand or betaori',
                      default='betaori')

    opts, _ = parser.parse_args()

    db_path = opts.data
    limit = opts.limit
    csv_file = opts.file_csv
    protocol = opts.protocol

    if not db_path:
        parser.error('Path to db is not given with -d flag.')

    parsers = {
        'betaori': BetaoriParser(),
        'tenpai': TenpaiParser(),
        'own_hand': OwnHandParser(),
    }

    logs_parser = parsers.get(protocol)

    if not logs_parser:
        parser.error('Possible values for protocol are: {}.'.format(','.join(parsers.keys())))

    print('Loading and decompressing logs content...')
    logs = load_logs(db_path, limit)

    if os.path.exists(csv_file):
        print('')
        print('Warning! {} already exists! New data will append there.'.format(csv_file))
        print('')
    else:
        with open(csv_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(logs_parser.csv_exporter.header())

    logs_count = 0
    samples_count = 0
    count_of_logs = len(logs)
    print(get_date_string())
    print('Starting processing...')

    for log_data in logs:
        if logs_count > 0 and logs_count % 1000 == 0:
            print('')
            print(get_date_string())
            print('Processed logs: {}/{}'.format(logs_count, count_of_logs))
            print('Samples: {}'.format(samples_count))

        game = logs_parser.get_game_hands(log_data['log_content'], log_data['log_id'])

        csv_records = logs_parser.extract_tenpai_players(game)
        save_csv_data(csv_records, csv_file)

        logs_count += 1
        samples_count += len(csv_records)

    print('End')
    print('Total samples:  {}'.format(samples_count))


def save_csv_data(csv_records, csv_file):
    with open(csv_file, 'a') as f:
        writer = csv.writer(f)
        for record in csv_records:
            writer.writerow(record)


def load_logs(db_path, limit):
    """
    Load logs from db and decompress logs content.
    How to download games content you can learn there: https://github.com/MahjongRepository/phoenix-logs
    """
    connection = sqlite3.connect(db_path)

    with connection:
        cursor = connection.cursor()
        if limit == 'unlimited':
            cursor.execute('SELECT log_id, log_content FROM logs where is_hirosima = 0;')
        else:
            limit = int(limit)
            cursor.execute('SELECT log_id, log_content FROM logs where is_hirosima = 0 LIMIT ?;', [limit])

        data = cursor.fetchall()

    results = []
    for x in data:
        results.append({
            'log_id': x[0],
            'log_content': bz2.decompress(x[1]).decode('utf-8')
        })

    return results


def get_date_string():
    return datetime.datetime.now().strftime('%H:%M:%S')


if __name__ == '__main__':
    main()
