import json
import logging
import os

import numpy as np
from agari_riichi_cost.protocol import AgariRiichiCostProtocol
from base.model import Model
from hickle import hickle
from mahjong.constants import EAST, SOUTH
from mahjong.hand_calculating.hand_config import HandConfig
from mahjong.hand_calculating.scores import ScoresCalculator
from sklearn.metrics import accuracy_score, mean_squared_error, precision_recall_fscore_support

logger = logging.getLogger("logs")


class AgariRiichiCostModel(Model):
    model_attributes = {
        "optimizer": "adam",
        "loss": "sparse_categorical_crossentropy",
        "metrics": ["accuracy"],
    }

    output = "softmax"
    units = 1024
    batch_size = 512

    input_size = AgariRiichiCostProtocol.input_size
    output_size = AgariRiichiCostProtocol.output_size

    def print_best_result(self):
        best_result = sorted(self.after_epoch_attrs, key=lambda x: x["empirical"], reverse=True)[0]
        logger.info("Best result")
        logger.info(json.dumps(best_result, indent=2))

    def calculate_predictions(self, model, epoch):
        real_indices = []
        predicted_indices = []

        data_files = os.listdir(self.data_path)
        correct_predictions = 0
        border_30_correct_predictions = 0
        border_20_correct_predictions = 0
        border_10_correct_predictions = 0
        for f in data_files:
            if not f.startswith("test_"):
                continue

            test_file_path = os.path.join(self.data_path, f)
            test_data = hickle.load(test_file_path)
            test_input = np.asarray(test_data["input_data"]).astype("float32")
            test_verification = test_data["verification_data"]

            predictions = model.predict(test_input, verbose=1)
            logger.info("predictions shape = {}".format(predictions.shape))

            for i, prediction in enumerate(predictions):
                original_cost, han, fu, is_dealer = test_verification[i]

                key = AgariRiichiCostProtocol.build_category_key(han, fu)
                real_index = AgariRiichiCostProtocol.HAND_COST_CATEGORIES[key]
                real_indices.append(real_index)

                predicted_index = np.argmax(prediction)
                predicted_key = sorted(
                    [
                        x[0]
                        for x in AgariRiichiCostProtocol.HAND_COST_CATEGORIES.items()
                        if x[1] == predicted_index
                    ]
                )[-1]
                if "-" in predicted_key:
                    han = int(predicted_key.split("-")[0])
                    fu = int(predicted_key.split("-")[1])
                else:
                    han = int(predicted_key)
                    fu = 0

                predicted_indices.append(predicted_index)

                hand = ScoresCalculator()
                player_wind = is_dealer and EAST or SOUTH
                config = HandConfig(player_wind=player_wind)
                predicted_cost = hand.calculate_scores(han=han, fu=fu, config=config)["main"]

                if is_dealer and self.is_dealer_hand_correctly_predicted(original_cost, predicted_cost):
                    correct_predictions += 1

                if not is_dealer and self.is_regular_hand_correctly_predicted(original_cost, predicted_cost):
                    correct_predictions += 1

                if self.error_border_predicted(original_cost, predicted_cost, 30):
                    border_30_correct_predictions += 1

                if self.error_border_predicted(original_cost, predicted_cost, 20):
                    border_20_correct_predictions += 1

                if self.error_border_predicted(original_cost, predicted_cost, 10):
                    border_10_correct_predictions += 1

        assert len(real_indices) == len(predicted_indices)

        accuracy = accuracy_score(real_indices, predicted_indices)

        precision, recall, fscore, _ = precision_recall_fscore_support(
            real_indices, predicted_indices, average="macro"
        )

        mean_squared_error_result = mean_squared_error(real_indices, predicted_indices)
        empirical_prediction = (correct_predictions / len(real_indices)) * 100
        border_30_correct_predictions = (border_30_correct_predictions / len(real_indices)) * 100
        border_20_correct_predictions = (border_20_correct_predictions / len(real_indices)) * 100
        border_10_correct_predictions = (border_10_correct_predictions / len(real_indices)) * 100

        logger.info("accuracy: {}".format(accuracy))
        logger.info("precision: {}".format(precision))
        logger.info("recall: {}".format(recall))
        logger.info("fscore (more is better): {}".format(fscore))
        logger.info("mean squared error: {}".format(mean_squared_error_result))
        logger.info(f"30%: {border_30_correct_predictions}")
        logger.info(f"20%: {border_20_correct_predictions}")
        logger.info(f"10%: {border_10_correct_predictions}")
        logger.info(f"empirical: {empirical_prediction}")

        if epoch:
            self.after_epoch_attrs.append(
                {
                    "epoch": epoch,
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "fscore": fscore,
                    "mean_squared_error": mean_squared_error_result,
                    "empirical": empirical_prediction,
                    "30": border_30_correct_predictions,
                    "20": border_20_correct_predictions,
                    "10": border_10_correct_predictions,
                }
            )

    def error_border_predicted(self, original_cost, predicted_cost, border_percentage):
        first_border = predicted_cost - round((predicted_cost / 100) * border_percentage)
        second_border = predicted_cost + round((predicted_cost / 100) * border_percentage)

        if first_border < original_cost < second_border:
            return True

        return False

    def is_dealer_hand_correctly_predicted(self, original_cost, predicted_cost):
        assert original_cost >= 2000

        if original_cost <= 3900 and predicted_cost <= 5800:
            return True

        if 3900 < original_cost <= 5800 and predicted_cost <= 7700:
            return True

        if 5800 < original_cost <= 7700 and 3900 <= predicted_cost <= 12000:
            return True

        if 7700 < original_cost <= 12000 and 5800 <= predicted_cost <= 18000:
            return True

        if 12000 < original_cost <= 18000 and 7700 <= predicted_cost <= 24000:
            return True

        if original_cost > 18000 and predicted_cost > 12000:
            return True

        return False

    def is_regular_hand_correctly_predicted(self, original_cost, predicted_cost):
        assert original_cost >= 1300

        if original_cost <= 2600 and predicted_cost <= 3900:
            return True

        if 2600 < original_cost <= 3900 and predicted_cost <= 5200:
            return True

        if 3900 < original_cost <= 5200 and 2600 <= predicted_cost <= 8000:
            return True

        if 5200 < original_cost <= 8000 and 3900 <= predicted_cost <= 12000:
            return True

        if 8000 < original_cost <= 12000 and 5200 <= predicted_cost <= 16000:
            return True

        if original_cost > 12000 and predicted_cost > 8000:
            return True

        return False
