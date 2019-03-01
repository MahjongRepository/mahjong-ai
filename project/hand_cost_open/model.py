import logging

from base.model import Model
from hand_cost_open.protocol import OpenHandCostProtocol

logger = logging.getLogger('logs')


class OpenHandCostModel(Model):
    model_name = 'hand_cost_open.h5'

    model_attributes = {
        'optimizer': 'sgd',
        'loss': 'mean_squared_error'
    }

    output = 'tanh'
    units = 1024
    batch_size = 256

    input_size = OpenHandCostProtocol.input_size

    def calculate_predictions(self, model, test_input, test_verification, epoch):
        predictions = model.predict(test_input, verbose=1)
        logger.info('predictions shape = {}'.format(predictions.shape))

        for prediction in predictions:
            print(prediction)
