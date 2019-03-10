import logging

from betaori_closed_hand.model import BetaoriClosedHandModel
from betaori_open_hand.protocol import BetaoriOpenHandProtocol

logger = logging.getLogger('logs')


class BetaoriOpenHandModel(BetaoriClosedHandModel):
    model_attributes = {
        'optimizer': 'sgd',
        'loss': 'mean_squared_error'
    }

    output = 'tanh'
    units = 1024
    batch_size = 256

    input_size = BetaoriOpenHandProtocol.input_size
    output_size = BetaoriOpenHandProtocol.output_size
