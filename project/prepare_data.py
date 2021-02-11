import gc
import logging
import os
import pathlib
import shutil
from optparse import OptionParser

import h5py
import hickle
import numpy as np
import pandas as pd
from agari_riichi_cost.protocol import AgariRiichiCostProtocol
from base.utils.logger import set_up_logging

logger = logging.getLogger("logs")


def main():
    parser = OptionParser()

    parser.add_option("-p", "--protocol", type="string")
    parser.add_option("-d", "--train-path", type="string", help="Path to .csv with train data.")
    parser.add_option("-t", "--test-path", type="string", help="Path to .csv with test data.")
    parser.add_option("-c", "--chunk", type="int", help="chunk size", default=100000)

    opts, _ = parser.parse_args()

    data_path = opts.train_path
    test_path = opts.test_path
    chunk_size = opts.chunk

    if not data_path:
        parser.error("Path to .csv with train data is not given.")

    if not test_path:
        parser.error("Path to .csv with test data is not given.")

    protocol_string = opts.protocol
    protocols = {
        "agari_riichi_cost": AgariRiichiCostProtocol,
    }

    protocol_class = protocols.get(protocol_string)

    if not protocol_class:
        parser.error(f"Possible values for protocol are: {', '.join(protocols.keys())}")

    set_up_logging("prepare_data")

    logger.info(f"{protocol_class.__name__} protocol will be used.")
    logger.info(f"Chunk size: {chunk_size}")

    processed_folder = pathlib.Path(__file__).parent / ".." / "processed_data"
    if not processed_folder.exists():
        os.mkdir(processed_folder)

    data_dir = processed_folder / protocol_string
    if data_dir.exists():
        logger.info("Data directory already exists. It was deleted.")
        shutil.rmtree(data_dir)

    os.mkdir(data_dir)

    for i, chunk in enumerate(pd.read_csv(test_path, chunksize=chunk_size, names=protocol_class.CSV_HEADER)):
        file_name = f"test_chunk_{i:03}.hkl"
        logger.info(f"Processing {file_name}...")

        protocol = protocol_class()

        chunk = chunk.replace([None, np.nan, "None", "NaN", "nan"], "")
        protocol.parse_new_data(chunk.iterrows())

        test_path = os.path.join(data_dir, file_name)
        hickle.dump(
            {
                "input_data": protocol.input_data,
                "output_data": protocol.output_data,
                "verification_data": protocol.verification_data,
            },
            test_path,
            mode="w",
        )

        logger.info(f"Test size = {len(protocol.input_data)}")

        del protocol
        gc.collect()

    logger.info("")
    logger.info("Processing train data...")

    for i, chunk in enumerate(pd.read_csv(data_path, chunksize=chunk_size, names=protocol_class.CSV_HEADER)):
        file_name = f"chunk_{i:03}.hkl"
        logger.info(f"Processing {file_name}...")

        protocol = protocols.get(protocol_string)
        protocol = protocol()

        chunk = chunk.replace([None, np.nan, "None", "NaN", "nan"], "")
        protocol.parse_new_data(chunk.iterrows())

        with h5py.File(os.path.join(data_dir, file_name), "w") as f:
            f.create_dataset("input_data", data=protocol.input_data, dtype="float32")
            f.create_dataset("output_data", data=protocol.output_data, dtype="float32")

        logger.info(f"Data size = {len(protocol.input_data)}")

        del protocol
        gc.collect()


if __name__ == "__main__":
    main()
