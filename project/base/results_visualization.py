import matplotlib.pyplot as plt


def show_graphs(data):
    epoch_key = 'epoch'

    fig = plt.figure(figsize=(10, 10))
    for i, value in enumerate(data.values()):
        fig.add_subplot(2, 1, i + 1)

        x_values = [x[epoch_key] for x in value]

        keys = [x for x in value[0].keys() if x != epoch_key]

        for key in keys:
            y_values = [x[key] for x in value]
            plt.plot(x_values, y_values, label=key)

        plt.legend()
        plt.xlabel('Epochs')

    plt.show()
