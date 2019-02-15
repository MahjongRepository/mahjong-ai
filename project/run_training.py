# -*- coding: utf-8 -*-
import os
from optparse import OptionParser

from base.logger import set_up_logging
from betaori.model import BetaoriModel
from own_hand.model import OwnHandModel


def main():
    parser = OptionParser()

    parser.add_option('-r',
                      '--rebuild',
                      action='store_true',
                      help='Do we need to rebuild model or not',
                      default=False)

    parser.add_option('-e',
                      '--epochs',
                      type='int',
                      default=16)

    parser.add_option('-v',
                      '--visualize',
                      action='store_true',
                      default=False)

    parser.add_option('-p', '--protocol',
                      type='string',
                      help='hand or betaori',
                      default='betaori')

    opts, _ = parser.parse_args()

    print_predictions = True
    rebuild = opts.rebuild
    epochs = opts.epochs
    protocol_string = opts.protocol
    visualize = opts.visualize

    root_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(root_dir, '..', 'processed_data')
    if not os.path.exists(data_dir):
        print('Directory with data is not exists. Run prepare_data.py')
        return

    if not os.listdir(data_dir):
        print('Directory with data is empty. Run prepare_data.py')
        return

    protocols = {
        'own_hand': OwnHandModel,
        'betaori': BetaoriModel,
    }

    protocol = protocols.get(protocol_string)

    if not protocol:
        parser.error('Possible values for protocol are: {}.'.format(','.join(protocols.keys())))

    set_up_logging('training_{}'.format(protocol_string))

    model = protocol(root_dir, data_dir, print_predictions, epochs, visualize)

    if rebuild:
        model.remove_model()

    model.run()


if __name__ == '__main__':
    main()
