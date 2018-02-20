# -*- coding: utf-8 -*-
import csv

from optparse import OptionParser

from keras import models
from keras import layers

import numpy as np

# states:
# 0 - unknown
# 1 - discard tsumogiri
# 2 - discard from hand
# 3 - discard after meld
# 4 - used in open set
states_num = 1
tiles_num = 136


def load_data(path):
    input_data = []
    output_data = []

    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # TODO: Sometimes we can find here empty waiting. It is a bug in parser
            if row['waiting'] and row['player_hand']:
                # TODO: This is the first experiment - given hand, find wait.
                # But actually we should give full info here, discards, etc.
                player_hand = [int(x) for x in row['player_hand'].split(',')]
                waiting_data = [int(x) for x in row['waiting'].split(',')]

                tiles = [0 for x in range(tiles_num * states_num)]
                for i in range(len(player_hand)):
                    # TODO: 0 here because we don't use states yet
                    tiles[0 * tiles_num + player_hand[i]] = 1

                input_data.append(tiles)

                waiting = [0 for x in range(tiles_num)]
                for wait in waiting_data:
                    waiting[wait] = 1

                output_data.append(waiting)

    return input_data, output_data


def print_predictions(model, test_input, test_output):
    predictions = model.predict(test_input, verbose=1)
    print("predictions shape = ", predictions.shape)

    i = 0
    for prediction in predictions:
        hand = []
        waits = []
        pred = []
        j = 0
        for prob in prediction:
            # TODO: 0.1?
            if prob > 0.1:
                pred.append(j)
            j += 1
        j = 0
        for inp in test_input[i]:
            if inp > 0.01:
                hand.append(j)
            j += 1
        j = 0
        for out in test_output[i]:
            if out > 0.01:
                waits.append(j)
            j += 1

        print("i =", i)
        print("hand:", hand)
        print("waits:", waits)
        print("preds:", pred)
        i += 1


def main():
    parser = OptionParser()

    parser.add_option('--train_path',
                      type='string',
                      help='Path to .csv with train data')

    parser.add_option('--test_path',
                      type='string',
                      help='Path to .csv with test data')

    parser.add_option('-p',
                      '--print_predictions',
                      action='store_true',
                      help='Print trained nn predictions on test data')

    opts, _ = parser.parse_args()

    train_logs_path = opts.train_path
    if not train_logs_path:
        parser.error('Path to input logs is not given.')

    test_logs_path = opts.test_path
    if not test_logs_path:
        parser.error('Path to test logs is not given.')

    print_predictions_flag = opts.print_predictions

    train_input_raw, train_output_raw = load_data(train_logs_path)
    test_input_raw, test_output_raw = load_data(test_logs_path)

    print("Train data size = %d, test data size = %d" % (len(train_input_raw), len(test_input_raw)))

    train_samples = len(train_input_raw)
    test_samples = len(test_input_raw)

    train_input = np.asarray(train_input_raw).astype('float32')
    train_output = np.asarray(train_output_raw).astype('float32')
    test_input = np.asarray(test_input_raw).astype('float32')
    test_output = np.asarray(test_output_raw).astype('float32')

    train_input = train_input.reshape((train_samples, tiles_num * states_num))
    test_input = test_input.reshape((test_samples, tiles_num * states_num))

    model = models.Sequential()
    model.add(layers.Dense(512, activation='relu', input_shape=(tiles_num * states_num,)))
    model.add(layers.Dense(tiles_num, activation='softmax'))

    model.compile(optimizer='rmsprop',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    model.fit(train_input, train_output, epochs=20, batch_size=512)

    results = model.evaluate(test_input, test_output, verbose=1)
    print("results [loss, acc] =", results)

    if print_predictions_flag is True:
        print_predictions(model, test_input, test_output)


if __name__ == '__main__':
    main()
