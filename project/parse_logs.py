# -*- coding: utf-8 -*-
import csv
import logging
import os
from optparse import OptionParser

from base.logger import set_up_logging
from base.utils import load_logs, save_csv_data
from betaori.parser import BetaoriParser
from own_hand.parser import OwnHandParser
from tenpai.parser import TenpaiParser

logger = logging.getLogger('logs')


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
                      default=None)

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

    set_up_logging('parser')
    
    logger.info('Loading and decompressing logs content...')
    logs = load_logs(db_path, limit)

    if os.path.exists(csv_file):
        logger.info('Warning! {} already exists! New data will append there.'.format(csv_file))
    else:
        with open(csv_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(logs_parser.csv_exporter.header())

    logs_count = 0
    samples_count = 0
    count_of_logs = len(logs)
    logger.info('Starting processing {} logs...'.format(count_of_logs))

    for log_data in logs:
        if logs_count > 0 and logs_count % 1000 == 0:
            logger.info('Processed logs: {}/{}'.format(logs_count, count_of_logs))
            logger.info('Samples: {}'.format(samples_count))

        game = logs_parser.get_game_hands(log_data['log_content'], log_data['log_id'])

        csv_records = logs_parser.extract_tenpai_players(game)
        save_csv_data(csv_records, csv_file)

        logs_count += 1
        samples_count += len(csv_records)

    logger.info('End')
    logger.info('Total samples:  {}'.format(samples_count))


if __name__ == '__main__':
    main()
