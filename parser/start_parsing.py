# -*- coding: utf-8 -*-
import logging
from optparse import OptionParser

from src.utils.logger import set_up_logging
from src.utils.utils import load_logs

logger = logging.getLogger('logs')


def main():
    parser = OptionParser()

    parser.add_option('-d', '--data',
                      type='string',
                      help='Path to .sqlite3 db with logs content')

    parser.add_option('-l', '--limit',
                      type='string',
                      help='For debugging',
                      default='unlimited')

    opts, _ = parser.parse_args()

    db_path = opts.data
    limit = opts.limit

    if not db_path:
        parser.error('Path to db is not given with -d flag.')

    set_up_logging('parser')

    logger.info('Loading and decompressing logs content...')
    logs = load_logs(db_path, limit)

    logs_count = 0
    samples_count = 0
    count_of_logs = len(logs)
    logger.info('Starting processing {} logs...'.format(count_of_logs))

    for log_data in logs:
        if logs_count > 0 and logs_count % 1000 == 0:
            logger.info('Processed logs: {}/{}'.format(logs_count, count_of_logs))
            logger.info('Samples: {}'.format(samples_count))

        print(log_data['log_content'])

    logger.info('End')
    logger.info('Total samples:  {}'.format(samples_count))


if __name__ == '__main__':
    main()
