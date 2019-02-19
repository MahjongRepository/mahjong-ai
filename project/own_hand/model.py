# -*- coding: utf-8 -*-
import logging

from base.model import Model
from own_hand.protocol import OwnHandProtocol

logger = logging.getLogger('logs')


class OwnHandModel(Model):
    model_name = 'own_hand.h5'

    model_attributes = {
        'optimizer': 'rmsprop',
        'loss': 'binary_crossentropy'
    }

    output = 'sigmoid'
    units = 1024
    batch_size = 512

    input_size = OwnHandProtocol.input_size

    def calculate_predictions(self, model, test_input, test_output, epoch):
        predictions = model.predict(test_input, verbose=1)
        logger.info('predictions shape = {}'.format(predictions.shape))

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
                wrong_predictions += 1
                # logger.info('wrong prediction on i = {}'.format(i))
                # logger.info('hand: {}'.format(TilesConverter.to_one_line_string(hand)))
                # logger.info('waits: {}'.format(TilesConverter.to_one_line_string(waits)))
                # logger.info('pred: {}'.format(TilesConverter.to_one_line_string(pred)))
                # logger.info('pred_sure: {}'.format(TilesConverter.to_one_line_string(pred_sure)))
                # logger.info('pred_unsure: {}'.format(TilesConverter.to_one_line_string(pred_unsure)))

            i += 1

        correct_predictions = i - wrong_predictions

        logger.info('Predictions: total = %d, correct = %d, wrong = %d' % (i, correct_predictions, wrong_predictions))
        logger.info('%% correct: %f' % (correct_predictions * 1.0 / i))
