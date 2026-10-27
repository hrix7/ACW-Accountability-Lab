"""Deterministic input fingerprints, not evidence-authenticity guarantees."""
import copy
import hashlib
import html
import json

from mhc import DEFAULT_WEIGHTS, weights


def fingerprint(value):
    """Hash parsed JSON using the documented Python serialization convention."""
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def build_provenance(cases, config=None):
    """Call after case/config validation; record the actual loaded objects."""
    config = {} if config is None else config
    effective = {
        'weights': weights(DEFAULT_WEIGHTS if config.get('weights') is None
                           else config['weights']),
        'threshold': config.get('threshold'),
        'floors': copy.deepcopy(config.get('floors') or {}),
    }
    return {
        'schema_version': 1,
        'fingerprint_format': 'sha256-python-json-sort-keys-compact-utf8-v1',
        'dataset_sha256': fingerprint(cases),
        'supplied_config_sha256': fingerprint(config),
        'effective_config': effective,
        'notice': ('Fingerprints identify parsed inputs, not original file bytes or '
                   'source truth. Preserve the dataset and configuration to reproduce '
                   'this report. Weights, floors and thresholds remain unvalidated.'),
    }


def render_provenance(provenance):
    if provenance is None:
        return ''
    return ('<details><summary>Reproducibility metadata</summary>'
            '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">' +
            html.escape(json.dumps(provenance, indent=2, ensure_ascii=False), quote=True) +
            '</pre></details>')
