# -*- coding: utf-8 -*-
import csv
import itertools
import os

from keras import layers
from keras import models
from keras.models import load_model
from mahjong.tile import TilesConverter
from optparse import OptionParser
import numpy as np

tiles_unique = 34
tiles_num = tiles_unique * 4
input_size = tiles_num * 5 + tiles_num * 5 * 2 + tiles_num + tiles_num // 4

model_path = 'betaori.h5'


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

    parser.add_option('-v',
                      '--visualize',
                      action='store_true',
                      help='Show model fitting history visualisation',
                      default=False)

    opts, _ = parser.parse_args()

    need_print_predictions = opts.print_predictions
    # need_visualize_history = opts.visualize
    rebuild = opts.rebuild

    temp_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')
    if not os.path.exists(temp_folder):
        print('Folder with data is not exists. Run split_csv.py')
        return

    csv_files = os.listdir(temp_folder)
    if not csv_files:
        print('Folder with data is empty. Run split_csv.py')
        return

    if rebuild and os.path.exists(model_path):
        print('Delete old model')
        os.remove(model_path)

    # remove test.csv with training files pool
    test_csv = csv_files.pop(csv_files.index('test.csv'))

    test_data = load_data(os.path.join(temp_folder, test_csv))
    test_input_raw, test_output_raw, test_verification = prepare_data(test_data)

    test_samples = len(test_input_raw)
    test_input = np.asarray(test_input_raw).astype('float32')
    test_output = np.asarray(test_output_raw).astype('float32')
    print('Test data size =', test_samples)

    if not os.path.exists(model_path):
        train_files = sorted(csv_files)
        print('{} files will be used for training'.format(len(train_files)))

        model = models.Sequential()
        # NB: need to configure
        model.add(layers.Dense(1024, activation='relu', input_shape=(input_size,)))
        model.add(layers.Dense(1024, activation='relu'))
        model.add(layers.Dense(tiles_unique, activation='tanh'))

        for train_file in train_files:
            print('')
            print('Processing {}...'.format(train_file))
            data_path = os.path.join(temp_folder, train_file)

            data = load_data(data_path)
            train_input_raw, train_output_raw, _ = prepare_data(data)

            train_samples = len(train_input_raw)
            train_input = np.asarray(train_input_raw).astype('float32')
            train_output = np.asarray(train_output_raw).astype('float32')

            print('Train data size =', train_samples)

            # NB: need to configure
            model.compile(optimizer='sgd',
                          loss='mean_squared_error',
                          metrics=['accuracy'])

            model.fit(train_input,
                      train_output,
                      epochs=16,
                      batch_size=256,
                      validation_data=(test_input, test_output))

        model.save(model_path)
    else:
        model = load_model(model_path)



    results = model.evaluate(test_input, test_output, verbose=1)
    print('results [loss, acc] =', results)

    calculate_predictions(model,
                          test_input,
                          test_output,
                          test_verification,
                          need_print_predictions)


def load_data(path):
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['tenpai_player_waiting']:
                data.append(row)
    return data


def process_discards(discards_data, melds_data, out_tiles):
    # For input we concatenate 5 rows of data for each player,
    # each row representing 136 tiles and their states:
    # First row - is discarded
    # Seconds row - tsumogiri flag
    # Third row - "after meld" flag
    # Fourth row - tile is present in open set
    # Fifth row - how long ago tile was discarded, 1 for first discad,
    #             and decreases by 0.025 for each following discard
    # NB: this should correspond to input_size variable!
    discards = [0 for x in range(tiles_num)]
    tsumogiri = [0 for x in range(tiles_num)]
    after_meld = [0 for x in range(tiles_num)]
    melds = [0 for x in range(tiles_num)]
    discards_order = [0 for x in range(tiles_num)]

    discard_order_value = 1
    discard_order_step = 0.025

    discards_temp = prepare_discards(discards_data)
    for x in discards_temp:
        tile = x[0]
        is_tsumogiri = x[1]
        is_after_meld = x[2]

        discards[tile] = 1
        tsumogiri[tile] = is_tsumogiri
        after_meld[tile] = is_after_meld
        discards_order[tile] = discard_order_value
        discard_order_value -= discard_order_step

        out_tiles[tile // 4] += 0.25

    melds_temp = prepare_melds(melds_data)
    for x in melds_temp:
        tiles = x[0]
        for tile in tiles:
            melds[tile] = 1

            out_tiles[tile // 4] += 0.25

    return discards, tsumogiri, after_meld, melds, discards_order, out_tiles


def prepare_discards(data):
    # sometimes we have empty discards
    # for example when other player is tenpai after first discard
    if not data:
        return []

    discards_temp = [x for x in data.split(',')]
    result = []
    for x in discards_temp:
        temp = x.split(';')
        result.append([
            # tile
            int(temp[0]),
            # is_tsumogiri
            int(temp[1]),
            # is_after_meld
            int(temp[2])
        ])
    return result


def prepare_melds(data):
    melds = []
    melds_temp = [x for x in data.split(',') if x]
    for x in melds_temp:
        temp = x.split(';')
        tiles = [int(x) for x in temp[1].split('/')]
        melds.append([
            tiles,
            # meld type
            temp[0]
        ])
    return melds


def prepare_data(raw_data):
    input_data = []
    output_data = []
    verification_data = []

    for row in raw_data:
        # total number of out tiles (all discards, all melds, player hand, dora indicators)
        out_tiles = [0 for x in range(tiles_num // 4)]

        discards, tsumogiri, after_meld, melds, discards_order, out_tiles = process_discards(
            row['tenpai_player_discards'],
            row['tenpai_player_melds'],
            out_tiles
        )

        sp_discards, sp_tsumogiri, sp_after_meld, sp_melds, sp_discards_order, out_tiles = process_discards(
            row['second_player_discards'],
            row['second_player_melds'],
            out_tiles
        )

        tp_discards, tp_tsumogiri, tp_after_meld, tp_melds, tp_discards_order, out_tiles = process_discards(
            row['third_player_discards'],
            row['third_player_melds'],
            out_tiles
        )

        player_hand = [0 for x in range(tiles_num)]
        for x in [int(x) for x in row['player_hand'].split(',')]:
            player_hand[x] += 1

            out_tiles[x // 4] += 0.25

        for x in [int(x) for x in row['dora_indicators'].split(',')]:
            out_tiles[x // 4] += 0.25

        input_cur = list(itertools.chain(
            discards,
            tsumogiri,
            after_meld,
            melds,
            discards_order,
            sp_discards,
            sp_tsumogiri,
            sp_after_meld,
            sp_melds,
            sp_discards_order,
            tp_discards,
            tp_tsumogiri,
            tp_after_meld,
            tp_melds,
            tp_discards_order,
            player_hand,
            out_tiles,
        ))

        if len(input_cur) != input_size:
            print("Internal error: len(input_cur) should be %d, but is %d" %
                  (input_size, len(input_cur)))
            exit(1)

        input_data.append(input_cur)

        # Output etalon - actual waits
        # For tiles that are not 100% safe and not actual waits,
        # we give value 0
        waiting = [0 for x in range(tiles_num // 4)]

        tenpai_discards = prepare_discards(row['tenpai_player_discards'])
        tenpai_melds = prepare_melds(row['tenpai_player_melds'])

        for x in tenpai_discards:
            # Here we give hint to network during training: tiles from discard
            # give output "-1":
            waiting[x[0] // 4] = -1

        waiting_temp = [x for x in row['tenpai_player_waiting'].split(',')]
        for x in waiting_temp:
            temp = x.split(';')
            tile = int(temp[0])
            # if cost == 0 it avgs that player can't win on this waiting
            # TODO: currently ignored
            # cost = int(temp[1])
            waiting[tile // 4] = 1

        output_data.append(waiting)

        # Use it only for visual debugging!
        tenpai_player_hand = [int(x) for x in row['tenpai_player_hand'].split(',')]

        verification_cur = []
        verification_cur.append(tenpai_player_hand)
        verification_cur.append(tenpai_discards)
        verification_cur.append(tenpai_melds)
        verification_cur.append(waiting_temp)

        verification_data.append(verification_cur)

    return input_data, output_data, verification_data


# TODO: probably this should be cleaned up and made part of TilesConverter class
def tiles_34_to_sting_unsorted(tiles):
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


def tiles_136_to_sting_unsorted(tiles):
    return tiles_34_to_sting_unsorted([x // 4 for x in tiles])


def calculate_predictions(model,
                          test_input,
                          test_output,
                          test_verification,
                          need_print_predictions):
    predictions = model.predict(test_input, verbose=1)
    print('predictions shape = ', predictions.shape)

    sum_min_wait_pos = 0
    sum_max_wait_pos = 0
    sum_avg_wait_pos = 0
    sum_genbutsu_error = 0
    i = 0
    for prediction in predictions:
        tiles_by_danger = np.argsort(prediction)

        hand = test_verification[i][0]

        discards = [x[0] for x in test_verification[i][1]]
        melds = [x[0] for x in test_verification[i][2]]

        waits = []
        waits_temp = test_verification[i][3]
        for x in waits_temp:
            temp = x.split(';')
            waits.append(int(temp[0]))

        sum_wait_pos = 0
        min_wait_pos = len(tiles_by_danger)
        max_wait_pos = 0
        for w in waits:
            pos = np.where(tiles_by_danger == (w // 4))[0].item(0)
            if pos < min_wait_pos:
                min_wait_pos = pos
            if pos > max_wait_pos:
                max_wait_pos = pos
            sum_wait_pos += pos

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
            print('============================================')
            print('hand:', TilesConverter.to_one_line_string(hand))
            print('discards:', tiles_136_to_sting_unsorted(discards))
            if melds:
                print('melds:', ' '.join([TilesConverter.to_one_line_string(x) for x in melds]))
            print('waits:', TilesConverter.to_one_line_string(waits))
            print('tiles_by_danger:', tiles_34_to_sting_unsorted(tiles_by_danger))
            print('min_wait_pos:', min_wait_pos)
            print('max_wait_pos:', max_wait_pos)
            print('avg_wait_pos:', avg_wait_pos)
            print('num_genbutsu:', num_genbutsu)
            print('avg_genbutsu_pos:', avg_genbutsu_pos)
            print('expected_avg_genbutsu_pos:', expected_avg_genbutsu_pos)
            print('genbutsu_error:', genbutsu_error)
            print('============================================')

        i += 1

        sum_min_wait_pos += min_wait_pos
        sum_max_wait_pos += max_wait_pos
        sum_avg_wait_pos += avg_wait_pos
        sum_genbutsu_error += sum_genbutsu_error

    avg_min_wait_pos = sum_min_wait_pos * 1.0 / i
    avg_max_wait_pos = sum_max_wait_pos * 1.0 / i
    avg_avg_wait_pos = sum_avg_wait_pos * 1.0 / i
    avg_genbutsu_error = sum_genbutsu_error * 1.0 / i

    print("Prediction results:")
    print("avg_min_wait_pos = %f (%f)" % (avg_min_wait_pos, avg_min_wait_pos / tiles_unique))
    print("avg_max_wait_pos = %f (%f)" % (avg_max_wait_pos, avg_max_wait_pos / tiles_unique))
    print("avg_avg_wait_pos = %f (%f)" % (avg_avg_wait_pos, avg_avg_wait_pos / tiles_unique))
    print("avg_genbutsu_error =", avg_genbutsu_error)


if __name__ == '__main__':
    main()
