import json
import logging
import os
import pickle
import shutil

import numpy as np
from keras import layers
from keras import models
from keras.models import load_model
from keras.utils import HDF5Matrix
from keras.callbacks import Callback

from base.results_visualization import show_graphs

logger = logging.getLogger('logs')


class Model:
    model_directory = None

    model_attributes = {}

    output = None
    units = None
    batch_size = None

    input_size = None
    output_size = None

    def __init__(self, input_directory_name, data_path, print_predictions, epochs, need_visualize, load_epoch):
        self.data_path = data_path
        self.print_predictions = print_predictions
        self.need_visualize = need_visualize
        self.load_epoch = load_epoch

        self.epochs = epochs

        self.graphs_data = {
            'first': [],
            'second': [],
            'third': [],
        }

        root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'models')
        if not os.path.exists(root_dir):
            os.mkdir(root_dir)

        self.model_directory = os.path.join(root_dir, input_directory_name)
        self.remove_model()

    def run(self):
        logger.info('Epochs: {}'.format(self.epochs))
        logger.info('Batch size: {}'.format(self.batch_size))
        logger.info('Model attributes: {}'.format(self.model_attributes))
        logger.info('Output: {}'.format(self.output))
        logger.info('Units: {}'.format(self.units))
        logger.info('')

        if self.load_epoch == 0:
            os.mkdir(self.model_directory)

            data_files_temp = os.listdir(self.data_path)
            data_files = []
            for f in data_files_temp:
                if not f.endswith('.h5'):
                    continue

                if f.startswith('test_'):
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
                        callbacks=[LoggingCallback(self.graphs_data)]
                    )

                logger.info('Predictions after epoch #{}'.format(n_epoch))
                self.calculate_predictions(model, n_epoch)

                # We save model after each epoch
                logger.info('Saving model, please don\'t interrupt...')
                model_path = os.path.join(self.model_directory, '{}_model.h5'.format(n_epoch))
                model.save(model_path)
                logger.info('Model saved')
        else:
            model_files = os.listdir(self.model_directory)
            model_file = None
            for f in model_files:
                if f.startswith('{}_'.format(self.load_epoch)):
                    model_file = f

            model = load_model(os.path.join(self.model_directory, model_file))
            self.calculate_predictions(model, None)

        if self.graphs_data.get('first'):
            self.print_best_result()

            logger.info(json.dumps(self.graphs_data))

            if self.need_visualize:
                show_graphs(self.graphs_data)

    def remove_model(self):
        if os.path.exists(self.model_directory) and self.load_epoch == 0:
            logger.info('Model directory already exists. It was deleted.')
            shutil.rmtree(self.model_directory)

    def create_and_compile_model(self):
        model = models.Sequential()
        model.add(layers.Dense(self.units, activation='relu', input_shape=(self.input_size,)))
        model.add(layers.Dense(self.units, activation='relu'))
        model.add(layers.Dense(self.output_size, activation=self.output))

        model.compile(**self.model_attributes)

        return model

    def calculate_predictions(self, model, epoch):
        pass

    def print_best_result(self):
        pass

    def tiles_34_to_sting_unsorted(self, tiles):
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

    def tiles_136_to_sting_unsorted(self, tiles):
        return self.tiles_34_to_sting_unsorted([x // 4 for x in tiles])


class LoggingCallback(Callback):

    def __init__(self, graphs_data):
        super(LoggingCallback, self).__init__()
        self.graphs_data = graphs_data

    def on_epoch_end(self, epoch, logs=None):
        msg = '{}'.format(', '.join('%s: %f' % (k, v) for k, v in logs.items()))
        logger.info(msg)

        n_epoch = len(self.graphs_data['third']) + 1
        logs['epoch'] = n_epoch
        self.graphs_data['third'].append(logs)
