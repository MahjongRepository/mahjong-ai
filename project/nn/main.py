# -*- coding: utf-8 -*-
import csv
import os
import time

from optparse import OptionParser

from keras import models
from keras import layers
from keras.models import load_model

import numpy as np

from mahjong.tile import TilesConverter

import matplotlib.pyplot as plt

# states:
# 0 - unknown
# 1 - discard tsumogiri
# 2 - discard from hand
# 3 - discard after meld
# 4 - used in open set
states_num = 1
tiles_unique = 34
tiles_num = tiles_unique * 4

model_path = 'model.h5'


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

                waiting = [0 for x in range(tiles_unique)]
                for wait in waiting_data:
                    waiting[wait // 4] = 1

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


def plot_history(history):
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs = range(1, len(loss) + 1)
    plt.plot(epochs, loss, 'bo', label='Training loss')
    plt.plot(epochs, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

    plt.clf()
    acc = history.history['acc']
    val_acc = history.history['val_acc']
    plt.plot(epochs, acc, 'bo', label='Training acc')
    plt.plot(epochs, val_acc, 'b', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()


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

    train_logs_path = opts.train_path
    if not train_logs_path:
        parser.error('Path to input logs is not given.')

    test_logs_path = opts.test_path
    if not test_logs_path:
        parser.error('Path to test logs is not given.')

    need_print_predictions = opts.print_predictions
    need_visualize_history = opts.visualize
    rebuild = opts.rebuild

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

    if rebuild and os.path.exists(model_path):
        print('Delete old model')
        os.remove(model_path)

    if not os.path.exists(model_path):
        model = models.Sequential()
        model.add(layers.Dense(1024, activation='relu', input_shape=(tiles_num * states_num,)))
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
            plot_history(history)
    else:
        print('Loading already existing model.')
        model = load_model(model_path)

    results = model.evaluate(test_input, test_output, verbose=1)
    print("results [loss, acc] =", results)

    if need_print_predictions:
        print_predictions(model, test_input, test_output)


if __name__ == '__main__':
    main()
