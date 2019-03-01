import os
from optparse import OptionParser

from base.utils.logger import set_up_logging
from betaori_closed_hand.model import BetaoriClosedHandModel
from betaori_open_hand.model import BetaoriOpenHandModel
from hand_cost_open.model import OpenHandCostModel


def main():
    parser = OptionParser()

    parser.add_option(
        '-p', '--protocol',
        type='string',
        default='betaori_closed_hand'
    )

    parser.add_option(
        '-i', '--input',
        type='string',
        help='The input directory name'
    )

    parser.add_option(
        '-e', '--epochs',
        type='int',
        default=16
    )

    parser.add_option(
        '--rebuild',
        action='store_true',
        help='Do we need to rebuild model or not',
        default=False
    )

    parser.add_option(
        '--print',
        action='store_true',
        help='Do we need to print predictions or not',
        default=False
    )

    parser.add_option(
        '--visualize',
        action='store_true',
        default=False
    )

    opts, _ = parser.parse_args()

    rebuild = opts.rebuild
    epochs = opts.epochs
    protocol_string = opts.protocol
    visualize = opts.visualize
    input_directory_name = opts.input
    print_predictions = opts.print

    root_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(root_dir, '..', 'processed_data', input_directory_name)
    if not os.path.exists(data_dir):
        print('Directory with data is not exists. Run prepare_data.py')
        return

    if not os.listdir(data_dir):
        print('Directory with data is empty. Run prepare_data.py')
        return

    protocols = {
        'betaori_closed_hand': BetaoriClosedHandModel,
        'betaori_open_hand': BetaoriOpenHandModel,
        'hand_cost_open': OpenHandCostModel,
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
