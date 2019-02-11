import csv


def main():
    reader = csv.DictReader(open('data/2017.csv', 'r'))

    data = {}
    total_data = 0

    for row in reader:
        # if row['count_melds'] == '0' and row['riichi'] == '0':
        if row['count_melds'] == '3':
            if row['step'] not in data:
                data[row['step']] = 0

            data[row['step']] += 1
            total_data += 1

    processed = []
    for key, value in data.items():
        v = (value / total_data) * 100
        processed.append([
            int(key),
            v,
        ])

    processed = sorted(processed, key=lambda x: x[0])

    for x in processed:
        print(x)
    print(total_data)


if __name__ == '__main__':
    main()
