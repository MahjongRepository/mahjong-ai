import logging

import numpy as np
import tensorflow as tf
from mahjong.tile import TilesConverter
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, mean_squared_error

from base.model import Model
from hand_cost_open.protocol import OpenHandCostProtocol

logger = logging.getLogger('logs')


class OpenHandCostModel(Model):
    model_name = 'hand_cost_open.h5'

    model_attributes = {
        'optimizer': 'adam',
        'loss': 'sparse_categorical_crossentropy',
        'metrics': ['accuracy']
    }

    output = 'softmax'
    units = 1024
    batch_size = 256

    input_size = OpenHandCostProtocol.input_size
    output_size = OpenHandCostProtocol.output_size

    def calculate_predictions(self, model, test_input, test_output, test_verification, epoch):
        predictions = model.predict(test_input, verbose=1)
        logger.info('predictions shape = {}'.format(predictions.shape))

        results_to_print = 50
        printed_results = 0

        real_indices = []
        predicted_indices = []

        for i, prediction in enumerate(predictions):
            tempai_hand = test_verification[i][0]
            discards = [x[0] for x in test_verification[i][1]]
            melds = [x[0] for x in test_verification[i][2]]
            dora_indicators = test_verification[i][5]
            tile, han, fu = test_verification[i][3]

            key = OpenHandCostProtocol.create_hand_cost_key(han, fu)
            real_index = OpenHandCostProtocol.hand_cost_mapping.get(key)

            predicted_index = np.argmax(prediction)

            real_indices.append(real_index)
            predicted_indices.append(predicted_index)

            if self.print_predictions and printed_results < results_to_print:
                predicted_value = prediction[predicted_index]
                if predicted_value > 0.70:
                    logger.info('dora indicators: {}'.format(TilesConverter.to_one_line_string(dora_indicators)))
                    logger.info('hand: {}'.format(TilesConverter.to_one_line_string(tempai_hand)))
                    if melds:
                        logger.info('melds: {}'.format(' '.join([TilesConverter.to_one_line_string(x) for x in melds])))
                    logger.info('discards: {}'.format(self.tiles_136_to_sting_unsorted(discards)))
                    logger.info('{}, {} han, {} fu, prediction {}'.format(TilesConverter.to_one_line_string([tile]), han, fu, predicted_value))

                    printed_results += 1

        with tf.Session() as session:
            confusion = tf.confusion_matrix(
                real_indices,
                predicted_indices
            )

            test_confusion = session.run(confusion)
            logger.info('confusion matrix: ')
            logger.info('\n' + '\n'.join([''.join(['{:8}'.format(item) for item in row]) for row in test_confusion]))

        accuracy = accuracy_score(
            real_indices,
            predicted_indices
        )

        precision, recall, fscore, _ = precision_recall_fscore_support(
            real_indices,
            predicted_indices,
            average='macro'
        )

        mean_squared_error_result = mean_squared_error(
            real_indices,
            predicted_indices,
        )

        logger.info('accuracy: {}'.format(accuracy))
        logger.info('precision: {}'.format(precision))
        logger.info('recall: {}'.format(recall))
        logger.info('fscore (more is better): {}'.format(fscore))
        logger.info('mean squared error: {}'.format(mean_squared_error_result))
