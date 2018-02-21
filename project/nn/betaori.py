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

model_path = 'model.h5'
test_data_percentage = 10


def main():
    parser = OptionParser()

    parser.add_option('--train_path',
                      type='string',
                      help='Path to .csv with data')

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

    data_path = opts.train_path
    if not data_path:
        parser.error('Path to input logs is not given.')

    need_print_predictions = opts.print_predictions
    need_visualize_history = opts.visualize
    rebuild = opts.rebuild

    train_data = load_data(data_path)

    test_data = []
    print('Original data size: {}'.format(len(train_data)))

    total_count = len(train_data)
    test_count = int((total_count / 100.0) * test_data_percentage)

    for x in range(0, test_count):
        index = random.randint(0, len(train_data) - 1)
        # delete element from input data and add it to test data
        test_data.append(train_data.pop(index))

    train_input_raw, train_output_raw = prepare_data(train_data)
    test_input_raw, test_output_raw = prepare_data(test_data)

    print("Train data size = %d, test data size = %d" % (len(train_input_raw), len(test_input_raw)))

    train_samples = len(train_input_raw)
    test_samples = len(test_input_raw)

    train_input = np.asarray(train_input_raw).astype('float32')
    train_output = np.asarray(train_output_raw).astype('float32')
    test_input = np.asarray(test_input_raw).astype('float32')
    test_output = np.asarray(test_output_raw).astype('float32')

    train_input = train_input.reshape((train_samples, tiles_num))
    test_input = test_input.reshape((test_samples, tiles_num))

    if rebuild and os.path.exists(model_path):
        print('Delete old model')
        os.remove(model_path)

    if not os.path.exists(model_path):
        model = models.Sequential()
        model.add(layers.Dense(1024, activation='relu', input_shape=(tiles_num,)))
        model.add(layers.Dense(1024, activation='relu'))
        model.add(layers.Dense(tiles_unique, activation='sigmoid'))

        model.compile(optimizer='rmsprop',
                      loss='binary_crossentropy',
                      metrics=['accuracy'])

        history = model.fit(train_input,
                            train_output,
                            epochs=20,
                            batch_size=512,
                            validation_data=(test_input, test_output))

        model.save(model_path)

        if need_visualize_history:
            plot_utils.plot_history(history)
    else:
        print('Loading already existing model.')
        model = load_model(model_path)

    results = model.evaluate(test_input, test_output, verbose=1)
    print("results [loss, acc] =", results)

    if need_print_predictions:
        print_predictions(model, test_input, test_output)


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

    for row in raw_data:
        player_hand = [int(x) for x in row['player_hand'].split(',')]

        waiting_temp = [x for x in row['waiting'].split(',')]
        waiting = []
        for x in waiting_temp:
            temp = x.split(';')
            tile = int(temp[0])
            # if cost == 0 it means that player can't win on this waiting
            cost = int(temp[1])

        player_wind = row['player_wind']
        round_wind = row['round_wind']

        melds_temp = [x for x in row['melds'].split(',')]
        melds = []
        for x in melds_temp:
            if not x:
                continue

            temp = x.split(';')
            meld_type = temp[0]
            tiles = [int(x) for x in temp[1].split(',')]

        discards_temp = [x for x in row['discards'].split(',')]
        discards = []
        for x in discards_temp:
            if not x:
                continue

            temp = x.split(';')
            tile = int(temp[0])
            is_tsumogiri = int(temp[1])
            after_meld = int(temp[2])

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
