import os
import pathlib
from optparse import OptionParser

from agari_riichi_cost.model import AgariRiichiCostModel
from base.utils.logger import set_up_logging


def main():
    parser = OptionParser()

    parser.add_option("-p", "--protocol", type="string")
    parser.add_option("-e", "--epochs", type="int", default=16)
    parser.add_option("--load", type="int", help="What epoch to load", default=0)
    parser.add_option(
        "--print",
        action="store_true",
        help="Do we need to print predictions or not",
        default=False,
    )
    parser.add_option("--visualize", action="store_true", default=False)

    opts, _ = parser.parse_args()

    load_epoch = opts.load
    epochs = opts.epochs
    protocol_string = opts.protocol
    visualize = opts.visualize
    print_predictions = opts.print

    data_dir = pathlib.Path(__file__).parent / ".." / "processed_data" / protocol_string
    if not os.path.exists(data_dir):
        print("Directory with data doesn't exist. Run prepare_data.py")
        return

    if not os.listdir(data_dir):
        print("Directory with data is empty. Run prepare_data.py")
        return

    protocols = {
        "agari_riichi_cost": AgariRiichiCostModel,
    }
    model_class = protocols.get(protocol_string)

    if not model_class:
        parser.error(f"Possible values for protocol are: {', '.join(protocols.keys())}.")

    set_up_logging("training_{}".format(protocol_string))

    model = model_class(protocol_string, data_dir, print_predictions, epochs, visualize, load_epoch)
    model.run()


if __name__ == "__main__":
    main()
