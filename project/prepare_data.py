import logging
import shutil
import subprocess
from optparse import OptionParser

import os

import gc
import h5py
import pickle
import pandas as pd
import numpy as np

from base.csv_exporter import CSVExporter
from base.utils.logger import set_up_logging
from betaori_closed_hand.protocol import BetaoriClosedHandProtocol
from betaori_open_hand.protocol import BetaoriOpenHandProtocol
from hand_cost_open.protocol import OpenHandCostProtocol

logger = logging.getLogger('logs')


def main():
    parser = OptionParser()

    parser.add_option(
        '-p', '--protocol',
        type='string',
         default='betaori_closed_hand'
    )

    parser.add_option(
        '-o', '--output',
        type='string',
        help='The output directory name'
    )

    parser.add_option(
        '-d', '--train-path',
        type='string',
        help='Path to .csv with train data.'
    )

    parser.add_option(
        '-t', '--test-path',
        type='string',
        help='Path to .csv with test data.'
    )

    parser.add_option(
        '--chunk',
        type='int',
        help='chunk size',
        default=100000
    )

    parser.add_option(
        '--percentage',
        type='int',
        help='test data percentage',
        default=5
    )

    opts, _ = parser.parse_args()

    data_path = opts.train_path
    test_path = opts.test_path
    chunk_size = opts.chunk
    test_data_percentage = opts.percentage
    output_directory_name = opts.output

    if not data_path:
        parser.error('Path to .csv with train data is not given.')

    if not test_path:
        parser.error('Path to .csv with test data is not given.')

    protocol_string = opts.protocol
    protocols = {
        'betaori_closed_hand': BetaoriClosedHandProtocol,
        'betaori_open_hand': BetaoriOpenHandProtocol,
        'hand_cost_open': OpenHandCostProtocol
    }

    protocol = protocols.get(protocol_string)

    if not protocol:
        parser.error('Possible values for protocol are: {}'.format(','.join(protocols.keys())))

    protocol = protocol()

    set_up_logging('prepare_data')
    
    logger.info('{} protocol will be used.'.format(protocol_string))
    logger.info('Chunk size: {}. Test data percentage: {}'.format(chunk_size, test_data_percentage))

    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'processed_data')
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    data_dir = os.path.join(root_dir, output_directory_name)
    if os.path.exists(data_dir):
        logger.info('Data directory already exists. It was deleted.')
        shutil.rmtree(data_dir)

    os.mkdir(data_dir)

    total_count = line_count(data_path)

    test_total_count = line_count(test_path)
    test_count = int((total_count / 100.0) * test_data_percentage)
    test_rows = np.random.choice(range(1, test_total_count), test_count, replace=False)
    skip_test_rows = list(set(range(0, test_total_count)) - set(test_rows))

    logger.info('Train data size: {}'.format(total_count))
    logger.info('Test data size: {}'.format(len(test_rows)))

    # pandas didn't add correct headers to csv by default
    # so we had to do it manually
    header = CSVExporter.header()

    # our test data had to be in separate file
    test_data = pd.read_csv(test_path, skiprows=skip_test_rows, names=header)
    test_data = test_data.replace([None, np.nan, 'None', 'NaN', 'nan'], '')

    protocol.parse_new_data(test_data.iterrows())

    protocol_test_path = os.path.join(data_dir, 'test.p')
    logger.info('Saving test.p...')
    pickle.dump(protocol, open(protocol_test_path, 'wb'))

    logger.info('')
    logger.info('Processing train data...')

    for i, chunk in enumerate(pd.read_csv(data_path, chunksize=chunk_size, names=header)):
        file_name = 'chunk_{:03}.h5'.format(i)
        logger.info('Processing {}...'.format(file_name))

        protocol = protocols.get(protocol_string)
        protocol = protocol()

        chunk = chunk.replace([None, np.nan, 'None', 'NaN', 'nan'], '')
        protocol.parse_new_data(chunk.iterrows())

        with h5py.File(os.path.join(data_dir, file_name), 'w') as f:
            f.create_dataset(
                'input_data',
                data=protocol.input_data,
                dtype='float32'
            )
            f.create_dataset(
                'output_data',
                data=protocol.output_data,
                dtype='float32'
            )

        logger.info('Data size = {}'.format(len(protocol.input_data)))

        gc.collect()


def line_count(file):
    return int(subprocess.check_output('wc -l {}'.format(file), shell=True).split()[0])


if __name__ == '__main__':
    main()
