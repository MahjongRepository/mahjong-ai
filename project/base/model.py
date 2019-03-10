import logging
import os
import pickle

import numpy as np
from keras import layers
from keras import models
from keras.models import load_model
from keras.utils import HDF5Matrix
from keras.callbacks import Callback

from base.results_visualization import show_graphs

logger = logging.getLogger('logs')


class Model:
    model_name = None

    model_attributes = {}

    output = None
    units = None
    batch_size = None

    input_size = None
    output_size = None

    def __init__(self, root_dir, data_path, print_predictions, epochs, need_visualize):
        self.model_path = os.path.join(root_dir, self.model_name)
        self.data_path = data_path
        self.print_predictions = print_predictions
        self.need_visualize = need_visualize

        self.epochs = epochs

        self.graphs_data = {
            'first': [],
            'second': [],
        }

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
        test_verification = test_data.verification_data
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
                        validation_data=(test_input, test_output),
                        callbacks=[LoggingCallback()]
                    )

                logger.info('Predictions after epoch #{}'.format(n_epoch))
                self.calculate_predictions(
                    model,
                    test_input,
                    test_output,
                    test_verification,
                    n_epoch
                )

                # We save model after each epoch
                logger.info('Saving model, please don\'t interrupt...')
                model.save(self.model_path)
                logger.info('Model saved')
        else:
            model = load_model(self.model_path)

        results = model.evaluate(test_input, test_output, verbose=1)
        logger.info('results [loss, acc] = {}'.format(results))

        self.calculate_predictions(model, test_input, test_output, test_verification, None)

        if self.graphs_data.get('first'):
            self.print_best_result()

        if self.need_visualize and self.graphs_data:
            show_graphs(self.graphs_data)

    def create_and_compile_model(self):
        model = models.Sequential()
        model.add(layers.Dense(self.units, activation='relu', input_shape=(self.input_size,)))
        model.add(layers.Dense(self.units, activation='relu'))
        model.add(layers.Dense(self.output_size, activation=self.output))

        model.compile(**self.model_attributes)

        return model

    def calculate_predictions(self, model, test_input, test_output, test_verification, epoch):
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

    def on_epoch_end(self, epoch, logs=None):
        msg = '{}'.format(', '.join('%s: %f' % (k, v) for k, v in logs.items()))
        logger.info(msg)
