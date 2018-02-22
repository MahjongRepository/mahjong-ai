# -*- coding: utf-8 -*-
import bz2
import csv
import json
import random
import sqlite3
import datetime
from optparse import OptionParser

import os
from threading import Thread

from parser.csv_exporter import CSVExporter
from parser.json_exporter import JsonExporter
from parser.parser import LogParser

data_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'visual', 'data')
if not os.path.exists(data_directory):
    os.mkdir(data_directory)


tenpai_players = []
threads_number = 6

parser = LogParser()


class ProcessLogsThread(Thread):

    def __init__(self, result_array, results, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.result_array = result_array
        self.results = results

    def run(self):
        processed = 0
        for log_data in self.results:
            if processed > 0 and processed % 1000 == 0:
                # TODO: Clear indication of already processed logs (from all threads)
                print('+100 processed logs')
            game = parser.get_game_hands(log_data['log_content'], log_data['log_id'])
            tenpai_players.extend(parser.extract_tenpai_players(game))
            processed += 1


def main():
    parser = OptionParser()

    parser.add_option('-p', '--path',
                      type='string',
                      help='Path to .sqlite3 db with logs content')

    parser.add_option('-e', '--exporter',
                      type='string',
                      help='Format to export data: json or csv',
                      default='json')

    parser.add_option('-f', '--file-csv',
                      type='string',
                      help='Where to save CSV')

    parser.add_option('-l', '--limit',
                      type='string',
                      help='For debugging',
                      default='unlimited')

    opts, _ = parser.parse_args()

    db_path = opts.path
    export_format = opts.exporter
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

    if os.path.exists(csv_file):
        print('')
        print('Warning! {} already exists'.format(csv_file))
        print('')
    else:
        # initial file header 
        if export_format == 'csv':
            with open(csv_file, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(CSVExporter.header())

    threads = []
    count_of_logs = len(logs)
    print('Starting processing...')

    part = int(count_of_logs / threads_number)
    for x in range(0, threads_number):
        start = x * part
        if (x + 1) != threads:
            end = (x + 1) * part
        else:
            # we had to add all remaining items to the last thread
            # for example with limit=81, threads=4 results will be distributed:
            # 20 20 20 21
            end = count_of_logs

        threads.append(ProcessLogsThread(tenpai_players, logs[start:end]))

    # let's start all threads
    for t in threads:
        t.start()

    # let's wait while all threads will be finished
    for t in threads:
        t.join()

    # TODO: Ability to save intermediate results to the csv
    # right now if something will happen during logs processing we will lose everything
    save_csv_data(tenpai_players, csv_file)


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


def save_csv_data(tenpai_players, csv_file):
    with open(csv_file, 'a') as f:
        writer = csv.writer(f)
        for player in tenpai_players:
            writer.writerow(CSVExporter.export_player(player))


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
