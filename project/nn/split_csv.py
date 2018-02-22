# -*- coding: utf-8 -*-
import csv
import random
import shutil
import subprocess
from optparse import OptionParser

import os
import pandas as pd
import numpy as np

test_data_percentage = 5
chunk_size = 50000


def main():
    parser = OptionParser()

    parser.add_option('-f', '--train-path',
                      type='string',
                      help='Path to .csv with train data.')

    opts, _ = parser.parse_args()

    data_path = opts.train_path
    if not data_path:
        parser.error('Path to .csv with train data is not given.')

    print('Chunk size: {}, test data percentage: {}'.format(chunk_size, test_data_percentage), end='\n\n')

    temp_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')
    if os.path.exists(temp_folder):
        print('Temp folder already exists. It was deleted.', end='\n\n')
        shutil.rmtree(temp_folder)

    os.mkdir(temp_folder)

    total_count = line_count(data_path)
    test_count = int((total_count / 100.0) * test_data_percentage)

    # remove from original data n% of rows
    data_rows = list(np.random.choice(np.arange(1, total_count + 1), (total_count - test_count), replace=False))
    # subtract from original data removed rows
    # we will get test rows with this operation
    test_rows = list(set([x for x in range(0, total_count)]) - set(data_rows))

    print('Original data size: {}'.format(total_count))
    print('Train data size: {}'.format(len(data_rows)))
    print('Test data size: {}'.format(len(test_rows)), end='\n\n')

    # our test data had to be in separate file
    # we need to skip data rows from original file to extract test data
    print('Saving test.csv...')
    test_data = pd.read_csv(data_path, skiprows=data_rows)
    test_data.to_csv(os.path.join(temp_folder, 'test.csv'), index=False)

    # pandas didn't add correct headers to csv by default
    # so we had to do it manually for chunks
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

    # it is important to skip test rows there
    # otherwise we will mix train and test data
    data = pd.read_csv(
        data_path,
        chunksize=chunk_size,
        skiprows=test_rows,
    )
    for i, chunk in enumerate(data):
        file_name = 'chunk_{:03}.csv'.format(i)
        print('Saving {}...'.format(file_name))
        chunk.to_csv(os.path.join(temp_folder, file_name), header=header, index=False)


def line_count(file):
    return int(subprocess.check_output('wc -l {}'.format(file), shell=True).split()[0])


if __name__ == '__main__':
    main()
