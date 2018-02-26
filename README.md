For now only **Python 3.5+** is supported.

# Data preparation

## How to get training data (phoenix logs)

You can find information about it there: https://github.com/MahjongRepository/phoenix-logs

## CSV exporter

`python prepare_data.py -p /path/to/db/2017.db -e csv -f output.csv`

Our main way to get data from replays.

# Neural network testing:

## Guess waits in own hand

1. `cd project/nn/`
2. `python prepare_data.py -f <path_to_data>.csv`
3. `python own_hand_waits.py [-p] [-r] [-v]`

`-r` - train model anew instead of trying to read saved model from file

`-v` - visualize loss and accuracy on training and validation data for all training epochs

`-p` - check NN guesses and print all mistakes

## Betaori

1. `cd project/nn/`
2. `python prepare_data.py -f <path_to_data>.csv`
2. `python betaori.py [-p] [-r] [-v]`

`-r` - train model anew instead of trying to read saved model from file

`-v` - visualize loss and accuracy on training and validation data for all training epochs

`-p` - check NN guesses and print all mistakes

# Visualisation

1. `cd project/visual/`
2. `sh start_server.sh`

It will run local http server and after this you will be able to check results of .json exporter work.
