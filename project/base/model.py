import csv
import logging
import os
import shutil

import tensorflow
import tensorflow_io as tfio
from keras import layers, models
from keras.models import load_model

logger = logging.getLogger("logs")


class Model:
    model_directory = None

    model_attributes = {}

    output = None
    units = None
    batch_size = None

    input_size = None
    output_size = None

    def __init__(
        self,
        input_directory_name,
        data_path,
        print_predictions,
        epochs,
        need_visualize,
        load_epoch,
    ):
        self.data_path = data_path
        self.print_predictions = print_predictions
        self.need_visualize = need_visualize
        self.load_epoch = load_epoch

        self.epochs = epochs

        self.after_epoch_attrs = []

        root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "models")
        if not os.path.exists(root_dir):
            os.mkdir(root_dir)

        self.model_directory = os.path.join(root_dir, input_directory_name)
        self.remove_model()

    def run(self):
        devices = tensorflow.config.list_physical_devices("GPU")
        assert len(devices) == 1, devices
        assert tensorflow.test.is_built_with_cuda()

        logger.info(f"Devices: {devices}")
        logger.info("Epochs: {}".format(self.epochs))
        logger.info("Batch size: {}".format(self.batch_size))
        logger.info("Model attributes: {}".format(self.model_attributes))
        logger.info("Output: {}".format(self.output))
        logger.info("Units: {}".format(self.units))
        logger.info("")

        if self.load_epoch == 0:
            os.mkdir(self.model_directory)

            data_files_temp = os.listdir(self.data_path)
            data_files = []
            for f in data_files_temp:
                if not f.endswith(".hkl"):
                    continue

                if f.startswith("test_"):
                    continue

                data_files.append(f)

            train_files = sorted(data_files)
            logger.info("{} files will be used for training".format(len(train_files)))

            model = self.create_and_compile_model()

            for n_epoch in range(1, self.epochs + 1):
                logger.info("")
                logger.info("Processing epoch #{}...".format(n_epoch))

                for train_file in train_files:
                    logger.info("Processing {}...".format(train_file))
                    h5_file_path = os.path.join(self.data_path, train_file)

                    x_train = tfio.IODataset.from_hdf5(h5_file_path, dataset="/input_data")
                    y_train = tfio.IODataset.from_hdf5(h5_file_path, dataset="/output_data")

                    train = (
                        tensorflow.data.Dataset.zip((x_train, y_train))
                        .batch(self.batch_size, drop_remainder=True)
                        .prefetch(tensorflow.data.experimental.AUTOTUNE)
                    )

                    model.fit(
                        train,
                        shuffle=True,
                        epochs=1,
                        batch_size=self.batch_size,
                    )

                logger.info("Predictions after epoch #{}".format(n_epoch))
                self.calculate_predictions(model, n_epoch)

                # We save model after each epoch
                logger.info("Saving model, please don't interrupt...")
                model_path = os.path.join(self.model_directory, "{}_model.h5".format(n_epoch))
                model.save(model_path)
                logger.info("Model saved")
        else:
            model_files = os.listdir(self.model_directory)
            model_file = None
            for f in model_files:
                if f.startswith("{}_".format(self.load_epoch)):
                    model_file = f

            model = load_model(os.path.join(self.model_directory, model_file))

        logger.info("Calculating predictions...")
        self.calculate_predictions(model, None)

        if self.after_epoch_attrs:
            self.print_best_result()
            csv_path = os.path.join(self.model_directory, "results.csv")
            with open(csv_path, "w") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=self.after_epoch_attrs[0].keys())
                writer.writeheader()
                for data in self.after_epoch_attrs:
                    writer.writerow(data)

    def remove_model(self):
        if os.path.exists(self.model_directory) and self.load_epoch == 0:
            logger.info("Model directory already exists. It was deleted.")
            shutil.rmtree(self.model_directory)

    def create_and_compile_model(self):
        model = models.Sequential()

        model.add(layers.Dense(self.units, activation="relu", input_shape=(self.input_size,)))
        model.add(layers.Dense(self.units, activation="relu"))
        model.add(layers.Dense(self.output_size, activation=self.output))

        model.compile(**self.model_attributes)
        return model

    def calculate_predictions(self, model, epoch):
        pass

    def print_best_result(self):
        pass
