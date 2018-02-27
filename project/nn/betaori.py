# -*- coding: utf-8 -*-
import csv
import itertools
import os
import pickle

from keras import layers
from keras import models
from keras.models import load_model
from mahjong.tile import TilesConverter
from optparse import OptionParser
import numpy as np

from protocol import tiles_unique
from protocol import input_size


model_path = 'betaori.h5'


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
    # need_visualize_history = opts.visualize
    rebuild = opts.rebuild

    temp_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')
    if not os.path.exists(temp_folder):
        print('Folder with data is not exists. Run prepare_data.py')
        return

    if not os.listdir(temp_folder):
        print('Folder with data is empty. Run prepare_data.py')
        return

    if rebuild and os.path.exists(model_path):
        print('Delete old model')
        os.remove(model_path)

    # remove test.p with training files pool
    test_file_path = os.path.join(temp_folder, 'test.p')
    test_data = pickle.load(open(test_file_path, "rb"))

    test_samples = len(test_data.input_data)
    test_input = np.asarray(test_data.input_data).astype('float32')
    test_output = np.asarray(test_data.output_data).astype('float32')
    test_verification = test_data.verification_data
    print('Test data size =', test_samples)

    if not os.path.exists(model_path):
        data_files_temp = os.listdir(temp_folder)
        data_files = []
        for f in data_files_temp:
            if not f.endswith('.p'):
                continue
            if f.endswith('test.p'):
                continue

            data_files.append(f)

        train_files = sorted(data_files)
        print('{} files will be used for training'.format(len(train_files)))

        model = models.Sequential()
        # NB: need to configure
        model.add(layers.Dense(1024, activation='relu', input_shape=(input_size,)))
        model.add(layers.Dense(1024, activation='relu'))
        model.add(layers.Dense(tiles_unique, activation='tanh'))

        for n_epoch in range(48):
            print('')
            print('Processing epoch #{}...'.format(n_epoch))
            for train_file in train_files:
                print('Processing {}...'.format(train_file))
                data_path = os.path.join(temp_folder, train_file)
                train_data = pickle.load(open(data_path, "rb"))

                train_samples = len(train_data.input_data)
                train_input = np.asarray(train_data.input_data).astype('float32')
                train_output = np.asarray(train_data.output_data).astype('float32')

                print('Train data size =', train_samples)

                # NB: need to configure
                # Need to try: sgd, adam, adagrad
                model.compile(optimizer='sgd',
                              loss='mean_squared_error')

                model.fit(train_input,
                          train_output,
                          epochs=1,
                          batch_size=256,
                          validation_data=(test_input, test_output))

            print('')
            print('Predictions after epoch #{}'.format(n_epoch))
            calculate_predictions(model,
                                  test_input,
                                  test_output,
                                  test_verification,
                                  False)

            print('')
            # We save model after each epoch
            print('Saving model, please don\'t interrupt...')
            model.save(model_path)
            print('Model saved')
    else:
        model = load_model(model_path)

    results = model.evaluate(test_input, test_output, verbose=1)
    print('results: loss =', results)

    print('Final predictions')
    calculate_predictions(model,
                          test_input,
                          test_output,
                          test_verification,
                          need_print_predictions)


# TODO: probably this should be cleaned up and made part of TilesConverter class
def tiles_34_to_sting_unsorted(tiles):
    string = ''
    for tile in tiles:
        if tile < 9:
            string += str(tile + 1) + 'm'
        elif 9 <= tile < 18:
            string += str(tile - 9 + 1) + 'p'
        elif 18 <= tile < 27:
            string += str(tile - 18 + 1) + 's'
        else:
            string += str(tile - 27 + 1) + 'z'

    return string


def tiles_136_to_sting_unsorted(tiles):
    return tiles_34_to_sting_unsorted([x // 4 for x in tiles])


def calculate_predictions(model,
                          test_input,
                          test_output,
                          test_verification,
                          need_print_predictions):
    predictions = model.predict(test_input, verbose=1)
    print('predictions shape = ', predictions.shape)

    sum_min_wait_pos = 0
    sum_max_wait_pos = 0
    sum_avg_wait_pos = 0
    sum_genbutsu_error = 0
    i = 0
    for prediction in predictions:
        tiles_by_danger = np.argsort(prediction)

        hand = test_verification[i][0]

        discards = [x[0] for x in test_verification[i][1]]
        melds = [x[0] for x in test_verification[i][2]]

        waits = []
        waits_temp = test_verification[i][3]
        for x in waits_temp:
            temp = x.split(';')
            waits.append(int(temp[0]))

        sum_wait_pos = 0
        min_wait_pos = len(tiles_by_danger)
        max_wait_pos = 0
        for w in waits:
            pos = np.where(tiles_by_danger == (w // 4))[0].item(0)
            if pos < min_wait_pos:
                min_wait_pos = pos
            if pos > max_wait_pos:
                max_wait_pos = pos
            sum_wait_pos += pos

        avg_wait_pos = sum_wait_pos / len(waits)

        unique_discards_34 = np.unique(np.array(discards) // 4)
        sum_genbutsu_pos = 0
        for d in unique_discards_34:
            pos = np.where(tiles_by_danger == d)[0].item(0)
            sum_genbutsu_pos += pos

        num_genbutsu = unique_discards_34.size
        avg_genbutsu_pos = sum_genbutsu_pos / num_genbutsu
        expected_avg_genbutsu_pos = (((num_genbutsu - 1) * num_genbutsu) / 2) / num_genbutsu
        genbutsu_error = avg_genbutsu_pos - expected_avg_genbutsu_pos

        if need_print_predictions:
            print('============================================')
            print('hand:', TilesConverter.to_one_line_string(hand))
            print('discards:', tiles_136_to_sting_unsorted(discards))
            if melds:
                print('melds:', ' '.join([TilesConverter.to_one_line_string(x) for x in melds]))
            print('waits:', TilesConverter.to_one_line_string(waits))
            print('tiles_by_danger:', tiles_34_to_sting_unsorted(tiles_by_danger))
            print('min_wait_pos:', min_wait_pos)
            print('max_wait_pos:', max_wait_pos)
            print('avg_wait_pos:', avg_wait_pos)
            print('num_genbutsu:', num_genbutsu)
            print('avg_genbutsu_pos:', avg_genbutsu_pos)
            print('expected_avg_genbutsu_pos:', expected_avg_genbutsu_pos)
            print('genbutsu_error:', genbutsu_error)
            print('============================================')

        i += 1

        sum_min_wait_pos += min_wait_pos
        sum_max_wait_pos += max_wait_pos
        sum_avg_wait_pos += avg_wait_pos
        sum_genbutsu_error += sum_genbutsu_error

    avg_min_wait_pos = sum_min_wait_pos * 1.0 / i
    avg_max_wait_pos = sum_max_wait_pos * 1.0 / i
    avg_avg_wait_pos = sum_avg_wait_pos * 1.0 / i
    avg_genbutsu_error = sum_genbutsu_error * 1.0 / i

    print("Prediction results:")
    print("avg_min_wait_pos = %f (%f)" % (avg_min_wait_pos, avg_min_wait_pos / tiles_unique))
    print("avg_max_wait_pos = %f (%f)" % (avg_max_wait_pos, avg_max_wait_pos / tiles_unique))
    print("avg_avg_wait_pos = %f (%f)" % (avg_avg_wait_pos, avg_avg_wait_pos / tiles_unique))
    print("avg_genbutsu_error =", avg_genbutsu_error)


if __name__ == '__main__':
    main()
