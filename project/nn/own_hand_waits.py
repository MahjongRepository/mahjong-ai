# -*- coding: utf-8 -*-
import csv
import os
import pickle

import numpy as np
from keras import layers
from keras import models
from keras.models import load_model
from mahjong.tile import TilesConverter

from nn.utils.protocols.own_hand_protocol import tiles_num, tiles_unique


class HandWaits(object):
    model_name = 'hand.h5'
    epochs = 16

    def __init__(self, root_dir, data_path, print_predictions):
        self.model_path = os.path.join(root_dir, self.model_name)
        self.data_path = os.path.join(data_path, 'hand')
        self.print_predictions = print_predictions

    def remove_model(self):
        if os.path.exists(self.model_path):
            os.remove(self.model_path)

    def run(self):
        test_file_path = os.path.join(self.data_path, 'test.p')
        test_data = pickle.load(open(test_file_path, 'rb'))

        test_samples = len(test_data.input_data)
        test_input = np.asarray(test_data.input_data).astype('float32')
        test_output = np.asarray(test_data.output_data).astype('float32')
        print('Test data size =', test_samples)

        if not os.path.exists(self.model_path):
            data_files_temp = os.listdir(self.data_path)
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
            model.add(layers.Dense(1024, activation='relu', input_shape=(tiles_num,)))
            model.add(layers.Dense(1024, activation='relu'))
            model.add(layers.Dense(tiles_unique, activation='sigmoid'))

            for n_epoch in range(self.epochs):
                print('')
                print('Processing epoch #{}...'.format(n_epoch))
                for train_file in train_files:
                    print('Processing {}...'.format(train_file))
                    data_path = os.path.join(self.data_path, train_file)
                    train_data = pickle.load(open(data_path, "rb"))

                    train_samples = len(train_data.input_data)
                    train_input = np.asarray(train_data.input_data).astype('float32')
                    train_output = np.asarray(train_data.output_data).astype('float32')

                    print('Train data size =', train_samples)

                    model.compile(
                        optimizer='rmsprop',
                        loss='binary_crossentropy',
                        metrics=['accuracy']
                    )

                    model.fit(
                        train_input,
                        train_output,
                        epochs=1,
                        batch_size=512,
                        validation_data=(test_input, test_output)
                    )

                # We save model after each epoch
                print('Saving model, please don\'t interrupt...')
                model.save(self.model_path)
                print('Model saved')
        else:
            model = load_model(self.model_path)

        results = model.evaluate(test_input, test_output, verbose=1)
        print('results [loss, acc] =', results)

        if self.print_predictions:
            self.calculate_predictions(model, test_input, test_output)

    def load_data(self, path):
        data = []
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['player_hand'] and row['waiting']:
                    data.append(row)
        return data

    def calculate_predictions(self, model, test_input, test_output):
        predictions = model.predict(test_input, verbose=1)
        print('predictions shape = ', predictions.shape)

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

            if set(waits) != set(pred):
                print('wrong prediction on i =', i)
                print('hand:', TilesConverter.to_one_line_string(hand))
                print('waits:', TilesConverter.to_one_line_string(waits))
                print('pred:', TilesConverter.to_one_line_string(pred))
                print('pred_sure:', TilesConverter.to_one_line_string(pred_sure))
                print('pred_unsure:', TilesConverter.to_one_line_string(pred_unsure))
                wrong_predictions += 1

            i += 1

        correct_predictions = i - wrong_predictions

        print('Predictions: total = %d, correct = %d, wrong = %d' % (i, correct_predictions, wrong_predictions))
        print('%% correct: %f' % (correct_predictions * 1.0 / i))
