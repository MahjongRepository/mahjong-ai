# -*- coding: utf-8 -*-
import logging
import os
import pickle

from keras import layers
from keras import models
from keras.callbacks import Callback
from keras.models import load_model
from keras.utils import HDF5Matrix
from mahjong.tile import TilesConverter
import numpy as np

from nn.utils.protocols.betaori_protocol import BetaoriProtocol

logger = logging.getLogger('logs')


class LoggingCallback(Callback):

    def on_epoch_end(self, epoch, logs={}):
        msg = '{}'.format(', '.join('%s: %f' % (k, v) for k, v in logs.items()))
        logger.info(msg)


class Betaori(object):
    model_name = 'betaori.h5'
    batch_size = 256

    def __init__(self, root_dir, data_path, print_predictions, epochs, chunk_size):
        self.model_path = os.path.join(root_dir, self.model_name)
        self.data_path = os.path.join(data_path, 'betaori')
        self.print_predictions = print_predictions

        self.epochs = epochs
        self.chunk_size = chunk_size

    def remove_model(self):
        if os.path.exists(self.model_path):
            os.remove(self.model_path)

    def run(self):
        model_attributes = {
            'optimizer': 'sgd',
            'loss': 'mean_squared_error'
        }

        logger.info('Epochs: {}'.format(self.epochs))
        logger.info('Chunk size: {}'.format(self.chunk_size))
        logger.info('Batch size: {}'.format(self.batch_size))
        logger.info('Model attributes: {}'.format(model_attributes))
        logger.info('')

        test_file_path = os.path.join(self.data_path, 'test.p')
        test_data = pickle.load(open(test_file_path, 'rb'))

        test_samples = len(test_data.input_data)
        test_input = np.asarray(test_data.input_data).astype('float32')
        test_output = np.asarray(test_data.output_data).astype('float32')
        test_verification = test_data.verification_data
        logger.info('Test data size = {}'.format(test_samples))

        if not os.path.exists(self.model_path):
            model = models.Sequential()
            model.add(layers.Dense(1024, activation='relu', input_shape=(BetaoriProtocol.input_size,)))
            model.add(layers.Dense(1024, activation='relu'))
            model.add(layers.Dense(BetaoriProtocol.tiles_unique, activation='tanh'))

            model.compile(**model_attributes)

            h5_file_path = os.path.join(self.data_path, 'data.h5')
            total_data_size = HDF5Matrix(h5_file_path, 'input_data').size
            number_of_examples = total_data_size // BetaoriProtocol.input_size
            logger.info('Train data size: {}'.format(number_of_examples))

            chunks = int(number_of_examples / self.chunk_size)
            # it happens when chunk_size > number_of_examples
            if chunks == 0:
                chunks = 1

            for n_epoch in range(self.epochs):
                logger.info('')
                logger.info('Processing epoch #{}...'.format(n_epoch))

                for x in range(0, chunks):
                    start = x * self.chunk_size
                    if x + 1 == chunks:
                        # we had to add all remaining items to the last chunk
                        # for example with limit=81, chunks=4 results will be distributed:
                        # 20 20 20 21
                        end = number_of_examples
                    else:
                        end = (x + 1) * self.chunk_size

                    logger.info('Data slice. Start = {}, end = {}'.format(start, end))

                    train_input = HDF5Matrix(h5_file_path, 'input_data', start=start, end=end)
                    train_output = HDF5Matrix(h5_file_path, 'output_data', start=start, end=end)

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
                self.calculate_predictions(model,
                                           test_input,
                                           test_output,
                                           test_verification,
                                           False)

                # We save model after each epoch
                logger.info('Saving model, please don\'t interrupt...')
                model.save(self.model_path)
                logger.info('Model saved')
        else:
            model = load_model(self.model_path)

        results = model.evaluate(test_input, test_output, verbose=1)
        logger.info('results: loss = {}'.format(results))

        logger.info('')
        logger.info('Final predictions')
        self.calculate_predictions(model,
                                   test_input,
                                   test_output,
                                   test_verification,
                                   self.print_predictions)

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

    def calculate_predictions(self,
                              model,
                              test_input,
                              test_output,
                              test_verification,
                              need_print_predictions):
        predictions = model.predict(test_input, verbose=1)
        logger.info('predictions shape = {}'.format(predictions.shape))

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
                logger.info('============================================')
                logger.info('hand: {}'.format(TilesConverter.to_one_line_string(hand)))
                logger.info('discards: {}'.format(self.tiles_136_to_sting_unsorted(discards)))
                if melds:
                    logger.info('melds: {}'.format(' '.join([TilesConverter.to_one_line_string(x) for x in melds])))
                logger.info('waits: {}'.format(TilesConverter.to_one_line_string(waits)))
                logger.info('tiles_by_danger: {}'.format(self.tiles_34_to_sting_unsorted(tiles_by_danger)))
                logger.info('min_wait_pos: {}'.format(min_wait_pos))
                logger.info('max_wait_pos: {}'.format(max_wait_pos))
                logger.info('avg_wait_pos: {}'.format(avg_wait_pos))
                logger.info('num_genbutsu: {}'.format(num_genbutsu))
                logger.info('avg_genbutsu_pos: {}'.format(avg_genbutsu_pos))
                logger.info('expected_avg_genbutsu_pos: {}'.format(expected_avg_genbutsu_pos))
                logger.info('genbutsu_error: {}'.format(genbutsu_error))
                logger.info('============================================')

            i += 1

            sum_min_wait_pos += min_wait_pos
            sum_max_wait_pos += max_wait_pos
            sum_avg_wait_pos += avg_wait_pos
            sum_genbutsu_error += genbutsu_error

        avg_min_wait_pos = sum_min_wait_pos * 1.0 / i
        avg_max_wait_pos = sum_max_wait_pos * 1.0 / i
        avg_avg_wait_pos = sum_avg_wait_pos * 1.0 / i
        avg_genbutsu_error = sum_genbutsu_error * 1.0 / i

        logger.info('Prediction results:')
        logger.info('avg_min_wait_pos = %f (%f)' % (avg_min_wait_pos, avg_min_wait_pos / BetaoriProtocol.tiles_unique))
        logger.info('avg_max_wait_pos = %f (%f)' % (avg_max_wait_pos, avg_max_wait_pos / BetaoriProtocol.tiles_unique))
        logger.info('avg_avg_wait_pos = %f (%f)' % (avg_avg_wait_pos, avg_avg_wait_pos / BetaoriProtocol.tiles_unique))
        logger.info('avg_genbutsu_error = {}'.format(avg_genbutsu_error))
