import logging
import os
import pickle

import numpy as np
from keras import layers
from keras import models
from keras.callbacks import Callback
from keras.models import load_model
from keras.utils import HDF5Matrix
from mahjong.tile import TilesConverter

from betaori.protocol import BetaoriProtocol
from betaori.results_visualization import plot_history

logger = logging.getLogger('logs')


class BetaoriModel:
    model_name = 'betaori.h5'

    model_attributes = {
        'optimizer': 'sgd',
        'loss': 'mean_squared_error'
    }

    output = 'tanh'
    units = 1024
    batch_size = 256

    input_size = BetaoriProtocol.input_size

    def __init__(self, root_dir, data_path, print_predictions, epochs, need_visualize):
        self.model_path = os.path.join(root_dir, self.model_name)
        self.data_path = data_path
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
                        validation_data=(test_input, test_output)
                    )

                logger.info('Predictions after epoch #{}'.format(n_epoch))
                self.calculate_predictions(
                    model,
                    test_input,
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

        self.calculate_predictions(model, test_input, test_verification, None)

        if self.need_visualize:
            plot_history(self.graphs_data)

    def create_and_compile_model(self):
        model = models.Sequential()
        model.add(layers.Dense(self.units, activation='relu', input_shape=(BetaoriProtocol.input_size,)))
        model.add(layers.Dense(self.units, activation='relu'))
        model.add(layers.Dense(BetaoriProtocol.tiles_unique, activation=self.output))

        model.compile(**self.model_attributes)

        return model

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

    def calculate_predictions(self, model, test_input, test_verification, epoch):
        predictions = model.predict(test_input, verbose=1)
        logger.info('predictions shape = {}'.format(predictions.shape))

        results_to_print = 10
        printed_results = 0

        sum_min_wait_position = 0
        sum_max_wait_position = 0
        sum_avg_wait_position = 0
        sum_genbutsu_error = 0
        sum_min_wait_position_in_hand = 0

        i = 0
        i_jap = 0
        for prediction in predictions:
            tiles_by_danger = np.argsort(prediction)

            tempai_hand = test_verification[i][0]

            discards = [x[0] for x in test_verification[i][1]]
            melds = [x[0] for x in test_verification[i][2]]

            waits = []
            waits_temp = test_verification[i][3]
            for x in waits_temp:
                temp = x.split(';')
                wait = int(temp[0])
                cost = int(temp[1])
                if cost > 0:
                    waits.append(wait)

            num_waits = len(waits)

            defending_hand = [x for x in test_verification[i][4]]
            defending_hand_unique = set(defending_hand)
            defending_hand_danger = []
            for t in defending_hand_unique:
                position = np.where(tiles_by_danger == t)[0].item(0)
                defending_hand_danger.append(position)
            defending_hand_danger = np.sort(defending_hand_danger)

            sum_wait_pos = 0
            min_wait_pos = len(tiles_by_danger)
            waits_in_hand = 0
            min_wait_pos_in_hand = len(tiles_by_danger)
            max_wait_pos = 0
            for waiting in waits:
                waiting = waiting // 4

                position = np.where(tiles_by_danger == waiting)[0].item(0)
                if position < min_wait_pos:
                    min_wait_pos = position
                if position > max_wait_pos:
                    max_wait_pos = position
                sum_wait_pos += position

                if waiting in defending_hand_unique:
                    waits_in_hand += 1
                    if position < min_wait_pos_in_hand:
                        min_wait_pos_in_hand = position

            min_wait_position_in_hand_coefficient = 0
            if 0 < waits_in_hand != len(defending_hand_unique):
                pos_in_hand = np.where(defending_hand_danger == min_wait_pos_in_hand)[0].item(0)
                min_wait_position_in_hand_coefficient = pos_in_hand / (len(defending_hand_unique) - waits_in_hand)
                i_jap += 1

            avg_wait_pos = sum_wait_pos / len(waits)

            unique_discards_34 = np.unique(np.array(discards) // 4)
            sum_genbutsu_pos = 0
            for d in unique_discards_34:
                position = np.where(tiles_by_danger == d)[0].item(0)
                sum_genbutsu_pos += position

            num_genbutsu = unique_discards_34.size
            avg_genbutsu_pos = sum_genbutsu_pos / num_genbutsu
            expected_avg_genbutsu_pos = (((num_genbutsu - 1) * num_genbutsu) / 2) / num_genbutsu
            genbutsu_error = avg_genbutsu_pos - expected_avg_genbutsu_pos

            if self.print_predictions and printed_results < results_to_print:
                logger.info('============================================')
                logger.info('defending_hand: {}'.format(TilesConverter.to_one_line_string([x * 4 for x in defending_hand])))
                logger.info('tempai_hand: {}'.format(TilesConverter.to_one_line_string(tempai_hand)))
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

                printed_results += 1

            avg_pos_offset = (((num_waits - 1) * num_waits) / 2) / num_waits

            # Here we adjust out values, so they are 0 in worst-case scenario
            # and 1 in best-case scenario
            sum_min_wait_position += (min_wait_pos / (BetaoriProtocol.tiles_unique - num_waits))
            sum_max_wait_position += ((max_wait_pos - num_waits) / (BetaoriProtocol.tiles_unique - num_waits))
            sum_avg_wait_position += ((avg_wait_pos - avg_pos_offset) / (BetaoriProtocol.tiles_unique - num_waits))
            sum_genbutsu_error += genbutsu_error
            sum_min_wait_position_in_hand += min_wait_position_in_hand_coefficient

            i += 1

        avg_min_wait_position = sum_min_wait_position / i
        avg_max_wait_position = sum_max_wait_position / i
        avg_avg_wait_position = sum_avg_wait_position / i
        avg_genbutsu_error = sum_genbutsu_error / i
        avg_min_wait_position_in_hand = sum_min_wait_position_in_hand / i_jap

        logger.info('Prediction results:')
        logger.info('avg_min_wait_position = {}'.format(avg_min_wait_position))
        logger.info('avg_max_wait_position = {}'.format(avg_max_wait_position))
        logger.info('avg_avg_wait_position = {}'.format(avg_avg_wait_position))
        logger.info('avg_genbutsu_error = {}'.format(avg_genbutsu_error))
        logger.info('avg_min_wait_pos_in_hand (jap metrics) = {}'.format(avg_min_wait_position_in_hand))

        if epoch:
            self.graphs_data.append(
                {
                    'epoch': epoch,
                    'avg_min_wait_pos': avg_min_wait_position,
                    'avg_max_wait_pos': avg_max_wait_position,
                    'avg_avg_wait_pos': avg_avg_wait_position,
                    'avg_genbutsu_error': avg_genbutsu_error,
                    'avg_min_wait_pos_in_hand': avg_min_wait_position_in_hand
                }
            )


class LoggingCallback(Callback):

    def on_epoch_end(self, epoch, logs=None):
        if not logs:
            return

        msg = '{}'.format(', '.join('%s: %f' % (k, v) for k, v in logs.items()))
        logger.info(msg)
