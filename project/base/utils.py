import bz2
import csv
import sqlite3

from mahjong.meld import Meld


def encode_discards(player_discards):
    discards = []
    for x in player_discards:
        discards.append('{};{};{};{};{}'.format(
            x.tile,
            x.is_tsumogiri and 1 or 0,
            x.after_meld and 1 or 0,
            x.after_riichi and 1 or 0,
            x.was_given_for_meld and 1 or 0,
            ))
    return ','.join(discards)


def encode_melds(player_melds):
    melds = []
    for meld in player_melds:
        meld_type = meld.type
        if meld_type == Meld.KAN and not meld.opened:
            meld_type = 'closed_kan'
        melds.append('{};{}'.format(meld_type, '/'.join([str(x) for x in meld.tiles])))
    return ','.join(melds)


def load_logs(db_path, limit):
    """
    Load logs from db and decompress logs content.
    How to download games content you can learn there: https://github.com/MahjongRepository/phoenix-logs
    """
    connection = sqlite3.connect(db_path)

    with connection:
        cursor = connection.cursor()
        if limit == 'unlimited':
            cursor.execute('SELECT log_id, log_content FROM logs where is_hirosima = 0;')
        else:
            limit = int(limit)
            cursor.execute('SELECT log_id, log_content FROM logs where is_hirosima = 0 LIMIT ?;', [limit])

        data = cursor.fetchall()

    results = []
    for x in data:
        results.append({
            'log_id': x[0],
            'log_content': bz2.decompress(x[1]).decode('utf-8')
        })

    return results


def save_csv_data(csv_records, csv_file):
    with open(csv_file, 'a') as f:
        writer = csv.writer(f)
        for record in csv_records:
            writer.writerow(record)
