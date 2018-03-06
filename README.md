For now only **Python 3.5+** is supported.

# Data preparation

## How to get training data (phoenix logs)

You can find information about it there: https://github.com/MahjongRepository/phoenix-logs

## Data parser

This script will prepare raw data for tests.

`python parse_data.py -d /path/to/db/2017.db -f output.csv`

## Prepare data for neural network tasks

1. `cd project`
2. `python prepare_data.py -f <path_to_train_data>.csv -t <path_to_test_data>.csv -p <task_name> [-c <val>] [-a <val>]`

`-p` - task name, can be one of: `own_hand` or `betaori`

`-c` - chunk size (by default, 100000)

`-a` - percentage of states from test_data.csv to use (by default, 5)

# Neural network scripts

## Guess waits in own hand

1. `cd project`
2. prepare data with `-p own_hand` parameter, e.g.

`python prepare_data.py -f <path_to_train_data>.csv -t <path_to_test_data>.csv -p own_hand`

3. `python run_own_hand_waits.py [-r] [-p]`

`-r` - train model anew instead of trying to read saved model from file

`-p` - check NN guesses and print all mistakes

## Betaori

1. `cd project`
2. prepare data with `-p betaori` parameter, e.g.

`python prepare_data.py -f <path_to_train_data>.csv -t <path_to_test_data>.csv -p betaori`

3. `python run_betaori.py [-r] [-p] [-e] [-v]`

`-r` - train model anew instead of trying to read saved model from file

`-p` - print all NN guesses

`-e` - number of epochs to use for training

`-v` - show training history visualization

# Visualisation

1. `cd project/visual/`
2. `sh start_server.sh`

It will run local http server and after this you will be able to check results of .json exporter work.
