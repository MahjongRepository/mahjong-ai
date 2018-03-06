# -*- coding: utf-8 -*-
import bz2
import csv
import json
import random
import sqlite3
import datetime
from optparse import OptionParser

import os

from parser.csv_exporter import CSVExporter
from parser.json_exporter import JsonExporter
from parser.parser import LogParser

data_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'visual', 'data')
if not os.path.exists(data_directory):
    os.mkdir(data_directory)


def main():
    parser = OptionParser()

    parser.add_option('-d', '--data',
                      type='string',
                      help='Path to .sqlite3 db with logs content')

    parser.add_option('-f', '--file-csv',
                      type='string',
                      help='Where to save CSV')

    parser.add_option('-l', '--limit',
                      type='string',
                      help='For debugging',
                      default='unlimited')

    opts, _ = parser.parse_args()

    db_path = opts.data
    export_format = 'csv'
    limit = opts.limit
    csv_file = opts.file_csv

    if not db_path:
        parser.error('Path to db is not given with -p flag.')

    if export_format not in ['json', 'csv']:
        parser.error('Not valid exported format. Supported formatters: json, csv')

    if export_format == 'csv' and not csv_file:
        parser.error('CSV file is not given with -f flag.')

    print('Loading and decompressing logs content...')
    logs = load_logs(db_path, limit)

    parser = LogParser()

    if os.path.exists(csv_file):
        print('')
        print('Warning! {} already exists!'.format(csv_file))
        print('')
    else:
        # initial file header
        if export_format == 'csv':
            with open(csv_file, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(CSVExporter.header())

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

        game = parser.get_game_hands(log_data['log_content'], log_data['log_id'])

        csv_records = parser.extract_tenpai_players(game)
        save_csv_data(csv_records, csv_file)

        logs_count += 1
        samples_count += len(csv_records)

    print('End')
    print('Total samples:  {}'.format(samples_count))


def save_json_data(tenpai_players):
    for player in tenpai_players:
        # there is no sense to store all data in .json format
        # for debug let's use only small number of tenpai hands
        if random.random() < 0.999:
            continue

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
