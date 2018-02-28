# -*- coding: utf-8 -*-
import os
from optparse import OptionParser

from nn.betaori import Betaori


def main():
    parser = OptionParser()

    parser.add_option('-p',
                      '--print_predictions',
                      action='store_true',
                      help='Print trained nn predictions on test data',
                      default=False)

    parser.add_option('-r',
                      '--rebuild',
                      action='store_true',
                      help='Do we need to rebuild model or not',
                      default=False)

    opts, _ = parser.parse_args()

    print_predictions = opts.print_predictions
    rebuild = opts.rebuild

    root_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(root_dir, 'processed_data')
    if not os.path.exists(data_dir):
        print('Directory with data is not exists. Run prepare_data.py')
        return

    if not os.listdir(data_dir):
        print('Directory with data is empty. Run prepare_data.py')
        return

    betaori = Betaori(root_dir, data_dir, print_predictions)

    if rebuild:
        betaori.remove_model()

    betaori.run()


if __name__ == '__main__':
    main()
