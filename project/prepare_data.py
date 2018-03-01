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

test_data_percentage = 5
chunk_size = 50000


def main():
    parser = OptionParser()

    parser.add_option('-f', '--train-path',
                      type='string',
                      help='Path to .csv with train data.')

    parser.add_option('-p', '--protocol',
                      type='string',
                      help='hand or betaori',
                      default='betaori')

    opts, _ = parser.parse_args()

    data_path = opts.train_path
    if not data_path:
        parser.error('Path to .csv with train data is not given.')

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
    test_count = int((total_count / 100.0) * test_data_percentage)

    # because of our data we need to select three values in a row
    test_count = round(test_count / 3)
    indices_with_step_three = list(range(1, total_count, 3))
    random_indices = np.random.choice(indices_with_step_three, test_count)
    test_rows = []
    for x in random_indices:
        test_rows.append(x)
        test_rows.append(x + 1)
        test_rows.append(x + 2)
    test_rows = set(list(test_rows))

    data_rows = list(set([x for x in range(0, total_count)]) - set(test_rows))
    train_data_size = len(data_rows)

    print('Original data size: {}'.format(total_count))
    print('Train data size: {}'.format(train_data_size))
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

    test_data = pd.read_csv(data_path, skiprows=data_rows, names=header)
    test_data = test_data.replace([None, np.nan, 'None', 'NaN', 'nan'], '')

    protocol.parse_new_data(test_data.iterrows())

    protocol_test_path = os.path.join(data_dir, 'test.p')
    print('Saving test.p...')
    pickle.dump(protocol, open(protocol_test_path, 'wb'))

    print('')
    print('Processing train data...')

    # it is important to skip test rows here
    # otherwise we will mix train and test data
    data = pd.read_csv(data_path, skiprows=test_rows, chunksize=chunk_size)

    f = h5py.File(os.path.join(data_dir, 'data.h5'), 'w')

    input_data = None
    output_data = None
    for i, chunk in enumerate(data):
        print('Processing chunk {}...'.format(i))

        if protocol_string == 'hand':
            protocol = OwnHandProtocol()
        else:
            protocol = BetaoriProtocol()

        chunk = chunk.replace([None, np.nan, 'None', 'NaN', 'nan'], '')
        protocol.parse_new_data(chunk.iterrows())

        if i == 0:
            input_data = f.create_dataset(
                'input_data',
                data=protocol.input_data,
                maxshape=(None, protocol.input_size),
                dtype='float32'
            )
            output_data = f.create_dataset(
                'output_data',
                data=protocol.output_data,
                maxshape=(None, protocol.tiles_unique),
                dtype='float32'
            )
        else:
            new_input = list(input_data[:]) + protocol.input_data
            input_data.resize(len(new_input), axis=0)
            input_data[:] = new_input

            new_output = list(output_data[:]) + protocol.output_data
            output_data.resize(len(new_output), axis=0)
            output_data[:] = new_output

        data_size = input_data.shape[0]
        print('Data size =', data_size)

        gc.collect()

    print('')
    print('Saving data.h5 file...')
    f.close()

    # validation
    # f = h5py.File(h5_file_path, 'r')
    # input_data = f['input_data']
    #
    # added_rows = []
    # for row in input_data:
    #     row_hash = str([x for x in row])
    #     if row_hash not in added_rows:
    #         added_rows.append(row_hash)
    #
    # print('')
    # print('Validation')
    # print('Data size =', data_size)
    # print('Unique rows =', len(added_rows))
    #
    # f.close()


def line_count(file):
    return int(subprocess.check_output('wc -l {}'.format(file), shell=True).split()[0])


if __name__ == '__main__':
    main()
