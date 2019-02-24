import datetime
import logging
import os


def set_up_logging(prefix):
    logs_directory = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
        '..',
        '..',
        'logs'
    )
    if not os.path.exists(logs_directory):
        os.mkdir(logs_directory)

    logger = logging.getLogger('logs')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    file_name = '{}_{}.log'.format(prefix, datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S'))
    fh = logging.FileHandler(os.path.join(logs_directory, file_name))
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
