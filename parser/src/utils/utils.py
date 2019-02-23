import bz2
import json
import sqlite3


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


class CompactJSONEncoder(json.JSONEncoder):
    """
    A JSON Encoder that puts small lists on single lines.
    """

    MAX_WIDTH = 180
    MAX_ITEMS = 20

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indentation_level = 0

    def encode(self, o):
        """
        Encode JSON object *o* with respect to single line lists.
        """
        if isinstance(o, (list, tuple)):
            if self._is_single_line_list(o):
                return "[" + ", ".join(json.dumps(el) for el in o) + "]"
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el) for el in o]
                self.indentation_level -= 1
                return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(o, dict):
            self.indentation_level += 1
            output = [self.indent_str + f"{json.dumps(k)}: {self.encode(v)}" for k, v in o.items()]
            self.indentation_level -= 1
            return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
        else:
            return json.dumps(o)

    def _is_single_line_list(self, o):
        return self._primitives_only(o) and len(o) <= self.MAX_ITEMS and len(str(o)) - 2 <= self.MAX_WIDTH

    def _primitives_only(self, o):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, (list, tuple, dict)) for el in o)

    @property
    def indent_str(self) -> str:
        return " " * self.indentation_level * self.indent
