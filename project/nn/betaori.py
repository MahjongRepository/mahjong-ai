# -*- coding: utf-8 -*-
import csv
import itertools
import os
import random
import time

from keras import layers
from keras import models
from keras.models import load_model
from mahjong.tile import TilesConverter
from optparse import OptionParser
import numpy as np

import plot_utils

tiles_unique = 34
tiles_num = tiles_unique * 4
input_size = tiles_num * 5

model_path = 'betaori.h5'
test_data_percentage = 10


def main():
    parser = OptionParser()

    parser.add_option('-p',
                      '--print_predictions',
                      action='store_true',
                      help='Print trained nn predictions on test data',
                      default=False)

    parser.add_option('-r',
                      '--rebuild',
                      action='store_true',
                      help='Do we need to rebuild model or not',
                      default=False)

    parser.add_option('-v',
                      '--visualize',
                      action='store_true',
                      help='Show model fitting history visualisation',
                      default=False)

    opts, _ = parser.parse_args()

    need_print_predictions = opts.print_predictions
    need_visualize_history = opts.visualize
    rebuild = opts.rebuild

    temp_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')
    if not os.path.exists(temp_folder):
        print('Folder with data is not exists. Run split_csv.py')
        return

    csv_files = os.listdir(temp_folder)
    if not csv_files:
        print('Folder with data is empty. Run split_csv.py')
        return

    if rebuild and os.path.exists(model_path):
        print('Delete old model')
        os.remove(model_path)

    # remove test.csv with training files pool
    test_csv = csv_files.pop(csv_files.index('test.csv'))

    if not os.path.exists(model_path):
        train_files = sorted(csv_files)
        print('{} files will be used for training'.format(len(train_files)))

        model = models.Sequential()
        # NB: need to configure
        model.add(layers.Dense(1024, activation='relu', input_shape=(input_size,)))
        model.add(layers.Dense(1024, activation='relu'))
        model.add(layers.Dense(tiles_unique, activation='tanh'))

        for train_file in train_files:
            print('')
            print('Processing {}...'.format(train_file))
            data_path = os.path.join(temp_folder, train_file)

            data = load_data(data_path)
            train_input_raw, train_output_raw, _ = prepare_data(data)

            train_samples = len(train_input_raw)
            train_input = np.asarray(train_input_raw).astype('float32')
            train_output = np.asarray(train_output_raw).astype('float32')

            print('Train data size =', train_samples)

            # NB: need to configure
            model.compile(optimizer='sgd',
                          loss='mean_squared_error',
                          metrics=['accuracy'])

            history = model.fit(train_input,
                                train_output,
                                epochs=16,
                                batch_size=256)

            # if need_visualize_history:
            #     plot_utils.plot_history(history)

        model.save(model_path)
    else:
        model = load_model(model_path)

    test_data = load_data(os.path.join(temp_folder, test_csv))
    test_input_raw, test_output_raw, test_verification = prepare_data(test_data)

    test_samples = len(test_input_raw)
    test_input = np.asarray(test_input_raw).astype('float32')
    test_output = np.asarray(test_output_raw).astype('float32')
    print('Test data size =', test_samples)

    results = model.evaluate(test_input, test_output, verbose=1)
    print('results [loss, acc] =', results)

    if need_print_predictions:
        print_predictions(model, test_input, test_output, test_verification)


def load_data(path):
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['waiting']:
                data.append(row)
    return data


def prepare_data(raw_data):
    input_data = []
    output_data = []
    verification_data = []

    for row in raw_data:
        # For input we concatenate 5 rows of data, each representing 136 tiles
        # and their states:
        # First row - is discarded
        # Seconds row - tsumogiri flag
        # Third row - "after meld" flag
        # Fourth row - tile is present in open set
        # Fifth row - how long ago tile was discarded, 1 for first discad,
        #             and decreases by 0.025 for each following discard
        # NB: this should correspond to input_size variable!
        discards = [0 for x in range(tiles_num)]
        tsumogiri = [0 for x in range(tiles_num)]
        after_meld = [0 for x in range(tiles_num)]
        melds = [0 for x in range(tiles_num)]
        discards_order = [0 for x in range(tiles_num)]

        # Output etalon - actual waits
        # For tiles that are not 100% safe and not actual waits,
        # we give value 0
        waiting = [0 for x in range(tiles_num // 4)]

        # TODO: currently ignored
        # player_wind = row['player_wind']
        # round_wind = row['round_wind']

        discard_order_value = 1
        discard_order_step = 0.025
        discards_temp = [x for x in row['discards'].split(',')]
        for x in discards_temp:
            temp = x.split(';')
            tile = int(temp[0])
            is_tsumogiri = int(temp[1])
            is_after_meld = int(temp[2])

            discards[tile] = 1
            tsumogiri[tile] = is_tsumogiri
            after_meld[tile] = is_after_meld
            discards_order[tile] = discard_order_value
            discard_order_value -= discard_order_step
            # Here we give hint to network during training: tiles from discard
            # give output "-1":
            waiting[tile // 4] = -1

        melds_temp = [x for x in row['melds'].split(',') if x]
        for x in melds_temp:
            temp = x.split(';')
            # meld_type = temp[0]
            tiles = [int(x) for x in temp[1].split('/')]
            for tile in tiles:
                melds[tile] = 1

        input_cur = list(itertools.chain(discards,
                                         tsumogiri,
                                         after_meld,
                                         melds,
                                         discards_order))
        if len(input_cur) != input_size:
            print("Internal error: len(input_cur) should be %d, but is %d" \
                  % (input_size, len(input_cur)))
            exit(1)

        input_data.append(input_cur)

        waiting_temp = [x for x in row['waiting'].split(',')]
        for x in waiting_temp:
            temp = x.split(';')
            tile = int(temp[0])
            # if cost == 0 it means that player can't win on this waiting
            # TODO: currently ignored
            # cost = int(temp[1])
            waiting[tile // 4] = 1

        output_data.append(waiting)

        player_hand = [int(x) for x in row['player_hand'].split(',')]

        verification_cur = []
        verification_cur.append(player_hand)
        verification_cur.append(discards_temp)
        verification_cur.append(melds_temp)
        verification_cur.append(waiting_temp)

        verification_data.append(verification_cur)

    return input_data, output_data, verification_data


# TODO: probably this should be cleaned up and made part of TilesConverter class
def tiles_34_to_sting_unsorted(tiles):
    string = ''
    for tile in tiles:
        if tile < 9:
            string += str(tile + 1) + 's'
        elif 9 <= tile < 18:
            string += str(tile - 9 + 1) + 'p'
        elif 18 <= tile < 27:
            string += str(tile - 18 + 1) + 'm'
        else:
            string += str(tile - 27 + 1) + 'z'

    return string


def print_predictions(model, test_input, test_output, test_verification):
    predictions = model.predict(test_input, verbose=1)
    print('predictions shape = ', predictions.shape)

    i = 0
    for prediction in predictions:
        tiles_by_danger = np.argsort(prediction)

        hand = test_verification[i][0]

        discards = []
        discards_temp = test_verification[i][1]
        for x in discards_temp:
            temp = x.split(';')
            tile = int(temp[0])
            # is_tsumogiri = int(temp[1])
            # is_after_meld = int(temp[2])

            discards.append(tile)

        melds = []
        melds_temp = test_verification[i][2]
        for x in melds_temp:
            temp = x.split(';')
            melds.append([int(x) for x in temp[1].split('/')])

        waits = []
        waits_temp = test_verification[i][3]
        for x in waits_temp:
            temp = x.split(';')
            waits.append(int(temp[0]))

        print('hand:', TilesConverter.to_one_line_string(hand))
        print('discards:', TilesConverter.to_one_line_string(discards))
        if melds:
            print('melds:', ' '.join([TilesConverter.to_one_line_string(x) for x in melds]))
        print('waits:', TilesConverter.to_one_line_string(waits))
        print('tiles_by_danger:', tiles_34_to_sting_unsorted(tiles_by_danger))
        print('============================================')

        i += 1


if __name__ == '__main__':
    main()
