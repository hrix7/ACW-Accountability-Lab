"""Strict JSON loading for auditable research inputs."""
import json
import math
from pathlib import Path


def loads_json(content):
    """Reject repeated keys and all non-finite numeric representations."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f'Non-finite JSON constant: {value}')

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f'Non-finite JSON number: {value}')
        return result

    return json.loads(content,
                      object_pairs_hook=unique_object,
                      parse_constant=reject_constant,
                      parse_float=finite_float)


def load_json(path):
    return loads_json(Path(path).read_text(encoding='utf-8'))
