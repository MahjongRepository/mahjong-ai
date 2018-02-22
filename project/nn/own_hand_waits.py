# -*- coding: utf-8 -*-
import csv
import os
import random
import time

from optparse import OptionParser

from keras import models
from keras import layers
from keras.models import load_model

import numpy as np

from mahjong.tile import TilesConverter

import plot_utils

tiles_unique = 34
tiles_num = tiles_unique * 4

model_path = 'hand.h5'
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
        model.add(layers.Dense(1024, activation='relu', input_shape=(tiles_num,)))
        model.add(layers.Dense(1024, activation='relu'))
        model.add(layers.Dense(tiles_unique, activation='sigmoid'))

        for train_file in train_files:
            print('')
            print('Processing {}...'.format(train_file))
            data_path = os.path.join(temp_folder, train_file)

            data = load_data(data_path)
            train_input_raw, train_output_raw = prepare_data(data)

            train_samples = len(train_input_raw)
            train_input = np.asarray(train_input_raw).astype('float32')
            train_output = np.asarray(train_output_raw).astype('float32')

            print('Train data size =', train_samples)

            model.compile(optimizer='rmsprop',
                          loss='binary_crossentropy',
                          metrics=['accuracy'])

            history = model.fit(
                train_input,
                train_output,
                epochs=20,
                batch_size=512
            )

            # if need_visualize_history:
            #     plot_utils.plot_history(history)

        model.save(model_path)
    else:
        model = load_model(model_path)

    test_data = load_data(os.path.join(temp_folder, test_csv))
    test_input_raw, test_output_raw = prepare_data(test_data)

    test_samples = len(test_input_raw)
    test_input = np.asarray(test_input_raw).astype('float32')
    test_output = np.asarray(test_output_raw).astype('float32')
    print('Test data size =', test_samples)

    results = model.evaluate(test_input, test_output, verbose=1)
    print('results [loss, acc] =', results)

    if need_print_predictions:
        print_predictions(model, test_input, test_output)


def load_data(path):
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['player_hand'] and row['waiting']:
                data.append(row)
    return data


def prepare_data(raw_data):
    input_data = []
    output_data = []

    for row in raw_data:
        # TODO: Sometimes we can find here empty waiting. It is a bug in parser
        if row['waiting'] and row['player_hand']:
            player_hand = [int(x) for x in row['player_hand'].split(',')]

            waiting = [0 for x in range(tiles_unique)]
            waiting_temp = [x for x in row['waiting'].split(',')]
            for x in waiting_temp:
                temp = x.split(';')
                tile = int(temp[0]) // 4
                waiting[tile] = 1

            tiles = [0 for x in range(tiles_num)]
            for i in range(len(player_hand)):
                tiles[player_hand[i]] = 1

            input_data.append(tiles)
            output_data.append(waiting)

    return input_data, output_data


def print_predictions(model, test_input, test_output):
    predictions = model.predict(test_input, verbose=1)
    print("predictions shape = ", predictions.shape)

    i = 0
    wrong_predictions = 0
    for prediction in predictions:
        hand = []
        waits = []
        pred = []
        pred_sure = []
        pred_unsure = []
        j = 0
        for prob in prediction:
            if prob > 0.8:
                pred_sure.append(j * 4)
            elif prob > 0.5:
                pred_unsure.append(j * 4)

            if prob > 0.5:
                pred.append(j * 4)

            j += 1
        j = 0
        for inp in test_input[i]:
            if inp > 0.01:
                hand.append(j)
            j += 1
        j = 0
        for out in test_output[i]:
            if out > 0.01:
                waits.append(j * 4)
            j += 1

        if (set(waits) != set(pred)):
            print("wrong prediction on i =", i)
            print("hand:", TilesConverter.to_one_line_string(hand))
            print("waits:", TilesConverter.to_one_line_string(waits))
            print("pred:", TilesConverter.to_one_line_string(pred))
            print("pred_sure:", TilesConverter.to_one_line_string(pred_sure))
            print("pred_unsure:", TilesConverter.to_one_line_string(pred_unsure))
            wrong_predictions += 1

        i += 1

    correct_predictions = i - wrong_predictions

    print("Predictions: total = %d, correct = %d, wrong = %d"
          % (i, correct_predictions, wrong_predictions))
    print("%% correct: %f" % (correct_predictions * 1.0 / i))


if __name__ == '__main__':
    main()
