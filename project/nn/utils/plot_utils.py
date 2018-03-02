import matplotlib.pyplot as plt


def plot_history(data):
    avg_min_wait_pos = [x['avg_min_wait_pos'] for x in data]
    avg_max_wait_pos = [x['avg_max_wait_pos'] for x in data]
    avg_avg_wait_pos = [x['avg_avg_wait_pos'] for x in data]
    epochs = [x['epoch'] for x in data]

    plt.plot(epochs, avg_min_wait_pos, label='Avg. min wait position')
    plt.plot(epochs, avg_max_wait_pos, label='Avg. max wait position')
    plt.plot(epochs, avg_avg_wait_pos, label='Avg. avg wait position')
    plt.title('Training results')
    plt.xlabel('Epochs')
    plt.ylabel('%')
    plt.legend()
    plt.show()
