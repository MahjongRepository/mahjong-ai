# -*- coding: utf-8 -*-
import csv
import shutil
import subprocess
from optparse import OptionParser

import os

import gc
import h5py
import pickle
import pandas as pd
import numpy as np

from nn.utils.protocols.betaori_protocol import BetaoriProtocol
from nn.utils.protocols.own_hand_protocol import OwnHandProtocol


def main():
    parser = OptionParser()

    parser.add_option('-f', '--train-path',
                      type='string',
                      help='Path to .csv with train data.')

    parser.add_option('-t', '--test-path',
                      type='string',
                      help='Path to .csv with test data.')

    parser.add_option('-p', '--protocol',
                      type='string',
                      help='hand or betaori',
                      default='betaori')

    parser.add_option('-c', '--chunk',
                      type='int',
                      help='chunk size',
                      default=100000)

    parser.add_option('-a', '--percentage',
                      type='int',
                      help='test data percentage',
                      default=5)

    opts, _ = parser.parse_args()

    data_path = opts.train_path
    test_path = opts.test_path
    chunk_size = opts.chunk
    test_data_percentage = opts.percentage

    if not data_path:
        parser.error('Path to .csv with train data is not given.')

    if not test_path:
        parser.error('Path to .csv with test data is not given.')

    protocol_string = opts.protocol
    if protocol_string not in ['hand', 'betaori']:
        parser.error('Protocol hand to be hand or betaori')

    print('{} protocol will be used.'.format(protocol_string))
    print('Chunk size: {}. Test data percentage: {}'.format(chunk_size, test_data_percentage), end='\n\n')

    root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'processed_data')
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)

    data_dir = os.path.join(root_dir, protocol_string)
    if os.path.exists(data_dir):
        print('Data directory already exists. It was deleted.', end='\n\n')
        shutil.rmtree(data_dir)

    os.mkdir(data_dir)

    total_count = line_count(data_path)

    test_total_count = line_count(test_path)
    test_count = int((total_count / 100.0) * test_data_percentage)
    test_rows = np.random.choice(range(1, test_total_count), test_count, replace=False)
    skip_test_rows = list(set(range(0, test_total_count)) - set(test_rows))

    print('Train data size: {}'.format(total_count))
    print('Test data size: {}'.format(len(test_rows)), end='\n\n')

    # pandas didn't add correct headers to csv by default
    # so we had to do it manually
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

    # our test data had to be in separate file
    # we need to skip data rows from original file to extract test data
    print('Preparing tests data...')
    if protocol_string == 'hand':
        protocol = OwnHandProtocol()
    else:
        protocol = BetaoriProtocol()

    test_data = pd.read_csv(test_path, skiprows=skip_test_rows, names=header)
    test_data = test_data.replace([None, np.nan, 'None', 'NaN', 'nan'], '')

    protocol.parse_new_data(test_data.iterrows())

    protocol_test_path = os.path.join(data_dir, 'test.p')
    print('Saving test.p...')
    pickle.dump(protocol, open(protocol_test_path, 'wb'))

    print('')
    print('Processing train data...')

    for i, chunk in enumerate(pd.read_csv(data_path, chunksize=chunk_size)):
        file_name = 'chunk_{:03}.h5'.format(i)
        print('Processing {}...'.format(file_name))

        if protocol_string == 'hand':
            protocol = OwnHandProtocol()
        else:
            protocol = BetaoriProtocol()

        chunk = chunk.replace([None, np.nan, 'None', 'NaN', 'nan'], '')
        protocol.parse_new_data(chunk.iterrows())

        with h5py.File(os.path.join(data_dir, file_name), 'w') as f:
            f.create_dataset(
                'input_data',
                data=protocol.input_data,
                maxshape=(None, protocol.input_size),
                dtype='float32'
            )
            f.create_dataset(
                'output_data',
                data=protocol.output_data,
                maxshape=(None, protocol.tiles_unique),
                dtype='float32'
            )

        print('Data size =', len(protocol.input_data))

        gc.collect()


def line_count(file):
    return int(subprocess.check_output('wc -l {}'.format(file), shell=True).split()[0])


if __name__ == '__main__':
    main()
