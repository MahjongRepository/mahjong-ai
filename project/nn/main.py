# -*- coding: utf-8 -*-

import os
import json

from optparse import OptionParser

from keras import models
from keras import layers

import numpy as np

# states:
# 0 - unknown
# 1 - discard tsumogiri
# 2 - discard from hand
# 3 - discard after meld
# 4 - used in open set
states_num = 1
tiles_num = 136

train_input_raw = []
train_output_raw = []
test_input_raw = []
test_output_raw = []


def parse_logs(path, input_raw, output_raw):
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            log_path = os.path.join(path, filename)
            with open(log_path) as log_file:
                json_data = json.load(log_file)
                for key, value in json_data.items():
                    # TODO: This is the first experiment - given hand,
                    # find wait.
                    # But actually we should give full info here, discards,
                    # etc.
                    if key.startswith("player_hand"):
                        tiles = [0 for x in range(tiles_num * states_num)]
                        for i in range(len(value)):
                            # TODO: 0 here because we don't use states yet
                            tiles[0 * tiles_num + value[i]] = 1
                        input_raw.append(tiles)
                    if key.startswith("waiting"):
                        waits = [0 for x in range(tiles_num)]
                        for i in range(len(value)):
                            for k, v in value[i].items():
                                if k.startswith("tile"):
                                    waits[v] = 1
                        output_raw.append(waits)
            continue
        else:
            continue


def main():
    parser = OptionParser()

    parser.add_option('--train_path',
                      type='string',
                      help='Path to folder with train logs')

    parser.add_option('--test_path',
                      type='string',
                      help='Path to folder with test logs')

    opts, _ = parser.parse_args()

    train_logs_path = opts.train_path
    if not train_logs_path:
        parser.error('Path to input logs is not given.')

    test_logs_path = opts.test_path
    if not test_logs_path:
        parser.error('Path to test logs is not given.')

    parse_logs(train_logs_path, train_input_raw, train_output_raw)
    parse_logs(test_logs_path, test_input_raw, test_output_raw)

    print("Train data size = %d, test data size = %d"
          % (len(train_input_raw), len(test_input_raw)))

    if (len(train_input_raw) != len(train_output_raw)) \
            or (len(test_input_raw) != len(test_output_raw)):
        print("Bad json file")
        return 1

    train_samples = len(train_input_raw)
    test_samples = len(test_input_raw)

    train_input = np.asarray(train_input_raw).astype('float32')
    train_output = np.asarray(train_output_raw).astype('float32')
    test_input = np.asarray(test_input_raw).astype('float32')
    test_output = np.asarray(test_output_raw).astype('float32')

    train_input = train_input.reshape((train_samples, tiles_num * states_num))
    test_input = test_input.reshape((test_samples, tiles_num * states_num))

    model = models.Sequential()
    model.add(layers.Dense(512, activation='relu', input_shape=(tiles_num * states_num,)))
    model.add(layers.Dense(tiles_num, activation='softmax'))

    model.compile(optimizer='rmsprop',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    model.fit(train_input, train_output, epochs=20, batch_size=512)

    results = model.evaluate(test_input, test_output)
    print("results [loss, acc] =", results)


if __name__ == '__main__':
    main()
