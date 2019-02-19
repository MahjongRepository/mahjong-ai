# -*- coding: utf-8 -*-
import logging

import numpy as np
from keras.callbacks import Callback
from mahjong.tile import TilesConverter

# from base.plot_utils import plot_history
from base.model import Model
from betaori.protocol import BetaoriProtocol

logger = logging.getLogger('logs')


class LoggingCallback(Callback):

    def on_epoch_end(self, epoch, logs={}):
        msg = '{}'.format(', '.join('%s: %f' % (k, v) for k, v in logs.items()))
        logger.info(msg)


class BetaoriModel(Model):
    model_name = 'betaori.h5'

    model_attributes = {
        'optimizer': 'sgd',
        'loss': 'mean_squared_error'
    }

    output = 'tanh'
    units = 1024
    batch_size = 256

    input_size = BetaoriProtocol.input_size

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
                              test_verification,
                              need_print_predictions,
                              epoch):
        predictions = model.predict(test_input, verbose=1)
        logger.info('predictions shape = {}'.format(predictions.shape))

        sum_min_wait_pos = 0
        sum_max_wait_pos = 0
        sum_avg_wait_pos = 0
        sum_genbutsu_error = 0
        sum_min_wait_pos_in_hand = 0
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
                pos = np.where(tiles_by_danger == t)[0].item(0)
                defending_hand_danger.append(pos)
            defending_hand_danger = np.sort(defending_hand_danger)

            sum_wait_pos = 0
            min_wait_pos = len(tiles_by_danger)
            waits_in_hand = 0
            min_wait_pos_in_hand = len(tiles_by_danger)
            max_wait_pos = 0
            for w in waits:
                pos = np.where(tiles_by_danger == (w // 4))[0].item(0)
                if pos < min_wait_pos:
                    min_wait_pos = pos
                if pos > max_wait_pos:
                    max_wait_pos = pos
                sum_wait_pos += pos

                if (w // 4) in defending_hand_unique:
                    waits_in_hand += 1
                    if pos < min_wait_pos_in_hand:
                        min_wait_pos_in_hand = pos

            min_wait_pos_in_hand_coef = 0
            if waits_in_hand > 0 and len(defending_hand_unique) != waits_in_hand:
                pos_in_hand = np.where(defending_hand_danger == min_wait_pos_in_hand)[0].item(0)
                min_wait_pos_in_hand_coef = pos_in_hand / (len(defending_hand_unique) - waits_in_hand)
                i_jap += 1

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
                logger.info('defending_hand: {}'.format(TilesConverter.to_one_line_string([x * 4 for x in defending_hand])))
                logger.info('tenpai_hand: {}'.format(TilesConverter.to_one_line_string(tempai_hand)))
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

            avg_pos_offset = (((num_waits - 1) * num_waits) / 2) / num_waits

            # Here we adjust out values, so they are 0 in worst-case scenario
            # and 1 in best-case scenario
            sum_min_wait_pos += (min_wait_pos / (BetaoriProtocol.tiles_unique - num_waits))
            sum_max_wait_pos += ((max_wait_pos - num_waits) / (BetaoriProtocol.tiles_unique - num_waits))
            sum_avg_wait_pos += ((avg_wait_pos - avg_pos_offset) / (BetaoriProtocol.tiles_unique - num_waits))
            sum_genbutsu_error += genbutsu_error
            sum_min_wait_pos_in_hand += min_wait_pos_in_hand_coef

            i += 1

        avg_min_wait_pos = sum_min_wait_pos / i
        avg_max_wait_pos = sum_max_wait_pos / i
        avg_avg_wait_pos = sum_avg_wait_pos / i
        avg_genbutsu_error = sum_genbutsu_error / i
        avg_min_wait_pos_in_hand = sum_min_wait_pos_in_hand / i_jap

        logger.info('Prediction results:')
        logger.info('avg_min_wait_pos = {}'.format(avg_min_wait_pos))
        logger.info('avg_max_wait_pos = {}'.format(avg_max_wait_pos))
        logger.info('avg_avg_wait_pos = {}'.format(avg_avg_wait_pos))
        logger.info('avg_genbutsu_error = {}'.format(avg_genbutsu_error))
        logger.info('avg_min_wait_pos_in_hand (jap metrics) = {}'.format(avg_min_wait_pos_in_hand))

        if epoch:
            self.graphs_data.append(
                {
                    'epoch': epoch,
                    'avg_min_wait_pos': avg_min_wait_pos,
                    'avg_max_wait_pos': avg_max_wait_pos,
                    'avg_avg_wait_pos': avg_avg_wait_pos,
                    'avg_genbutsu_error': avg_genbutsu_error,
                    'avg_min_wait_pos_in_hand': avg_min_wait_pos_in_hand
                }
            )
