import json
import logging

import numpy as np
from mahjong.tile import TilesConverter

from base.model import Model
from betaori_closed_hand.protocol import BetaoriClosedHandProtocol

logger = logging.getLogger('logs')


class BetaoriClosedHandModel(Model):
    model_attributes = {
        'optimizer': 'sgd',
        'loss': 'mean_squared_error'
    }

    output = 'tanh'
    units = 1024
    batch_size = 256

    input_size = BetaoriClosedHandProtocol.input_size
    output_size = BetaoriClosedHandProtocol.output_size

    def print_best_result(self):
        best_result = sorted(self.graphs_data['first'], key=lambda x: x['avg_min_wait_pos'], reverse=True)[0]
        logger.info('Best result')
        logger.info(json.dumps(best_result, indent=2))

        second = [x for x in self.graphs_data['second'] if x['epoch'] == best_result['epoch']]
        third = [x for x in self.graphs_data['third'] if x['epoch'] == best_result['epoch']]

        logger.info('Second value')
        logger.info(json.dumps(second, indent=2))

        logger.info('Model attrs')
        logger.info(json.dumps(third, indent=2))

    def calculate_predictions(self, model, test_input, test_output, test_verification, epoch):
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
            sum_min_wait_position += (min_wait_pos / (BetaoriClosedHandProtocol.tiles_unique - num_waits))
            sum_max_wait_position += ((max_wait_pos - num_waits) / (BetaoriClosedHandProtocol.tiles_unique - num_waits))
            sum_avg_wait_position += ((avg_wait_pos - avg_pos_offset) / (BetaoriClosedHandProtocol.tiles_unique - num_waits))
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
            self.graphs_data['first'].append(
                {
                    'epoch': epoch,
                    'avg_min_wait_pos': avg_min_wait_position,
                    'avg_max_wait_pos': avg_max_wait_position,
                    'avg_avg_wait_pos': avg_avg_wait_position,
                    'jap_metric': avg_min_wait_position_in_hand
                }
            )

            self.graphs_data['second'].append(
                {
                    'epoch': epoch,
                    'avg_genbutsu_error': avg_genbutsu_error,
                }
            )
