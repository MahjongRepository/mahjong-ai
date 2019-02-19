# -*- coding: utf-8 -*-
import logging
import os
import pickle

import numpy as np
from keras import layers
from keras import models
from keras.models import load_model
from keras.utils import HDF5Matrix
from mahjong.tile import TilesConverter

from own_hand.protocol import OwnHandProtocol

logger = logging.getLogger('logs')


class Model:
    model_name = None

    model_attributes = {}

    output = None
    units = 0
    batch_size = 0

    input_size = 0

    def __init__(self, root_dir, data_path, print_predictions, epochs, need_visualize):
        self.model_path = os.path.join(root_dir, self.model_name)
        self.data_path = os.path.join(data_path, 'own_hand')
        self.print_predictions = print_predictions
        self.need_visualize = need_visualize

        self.epochs = epochs

        self.graphs_data = []

    def remove_model(self):
        if os.path.exists(self.model_path):
            os.remove(self.model_path)

    def run(self):
        logger.info('Epochs: {}'.format(self.epochs))
        logger.info('Batch size: {}'.format(self.batch_size))
        logger.info('Model attributes: {}'.format(self.model_attributes))
        logger.info('Output: {}'.format(self.output))
        logger.info('Units: {}'.format(self.units))
        logger.info('')

        test_file_path = os.path.join(self.data_path, 'test.p')
        test_data = pickle.load(open(test_file_path, 'rb'))

        test_samples = len(test_data.input_data)
        test_input = np.asarray(test_data.input_data).astype('float32')
        test_output = np.asarray(test_data.output_data).astype('float32')
        logger.info('Test data size = {}'.format(test_samples))

        if not os.path.exists(self.model_path):
            data_files_temp = os.listdir(self.data_path)
            data_files = []
            for f in data_files_temp:
                if not f.endswith('.h5'):
                    continue

                data_files.append(f)

            train_files = sorted(data_files)
            logger.info('{} files will be used for training'.format(len(train_files)))

            model = self.create_and_compile_model()

            for n_epoch in range(1, self.epochs + 1):
                logger.info('')
                logger.info('Processing epoch #{}...'.format(n_epoch))

                for train_file in train_files:
                    logger.info('Processing {}...'.format(train_file))
                    h5_file_path = os.path.join(self.data_path, train_file)

                    train_input = HDF5Matrix(h5_file_path, 'input_data')
                    train_output = HDF5Matrix(h5_file_path, 'output_data')

                    logger.info('Train data size = {}'.format(train_input.size / self.input_size))

                    model.fit(
                        train_input,
                        train_output,
                        # we need it to work with md5 data
                        shuffle='batch',
                        epochs=1,
                        batch_size=self.batch_size,
                        validation_data=(test_input, test_output)
                    )

                logger.info('Predictions after epoch #{}'.format(n_epoch))
                self.calculate_predictions(model,
                                           test_input,
                                           test_output,
                                           n_epoch)

                # We save model after each epoch
                logger.info('Saving model, please don\'t interrupt...')
                model.save(self.model_path)
                logger.info('Model saved')
        else:
            model = load_model(self.model_path)

        results = model.evaluate(test_input, test_output, verbose=1)
        logger.info('results [loss, acc] = {}'.format(results))

        self.calculate_predictions(model, test_input, test_output, None)

    def create_and_compile_model(self):
        model = models.Sequential()
        model.add(layers.Dense(self.units, activation='relu', input_shape=(OwnHandProtocol.input_size,)))
        model.add(layers.Dense(self.units, activation='relu'))
        model.add(layers.Dense(OwnHandProtocol.tiles_unique, activation=self.output))

        model.compile(**self.model_attributes)

        return model

    def calculate_predictions(self, model, test_input, test_output, epoch):
        pass