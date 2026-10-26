"""Preview and apply an auditable multi-edit draft to synthetic case records."""
import argparse
import copy
import json
from pathlib import Path

from case_io import export_cases, load_cases
from editor import apply_rating_edit
from strict_json import load_json


CHANGE_FIELDS = {'case_id', 'group', 'dimension', 'value', 'rationale', 'confidence'}


def apply_draft(cases, changes):
    """Validate all edits on a copy and return (edited_cases, change_audit)."""
    if not isinstance(changes, list) or not changes:
        raise ValueError('Draft must be a nonempty list of changes')
    edited = copy.deepcopy(cases)
    audit = []
    targets = set()
    for index, change in enumerate(changes, start=1):
        if not isinstance(change, dict) or set(change) != CHANGE_FIELDS:
            raise ValueError(f'Change {index} requires exactly {sorted(CHANGE_FIELDS)}')
        target = (change['case_id'], change['group'], change['dimension'])
        if target in targets:
            raise ValueError(f'Change {index} repeats target {target}')
        targets.add(target)
        matches = [case for case in edited if case['id'] == change['case_id']]
        if len(matches) != 1:
            raise ValueError(f'Change {index} has an unknown case ID')
        before = copy.deepcopy(matches[0][change['group']][change['dimension']]) \
            if change['group'] in matches[0] and change['dimension'] in matches[0][change['group']] \
            else None
        raw_value = 'unknown' if change['value'] is None else str(change['value'])
        edited = apply_rating_edit(
            edited, change['case_id'], change['group'], change['dimension'],
            raw_value, change['rationale'], change['confidence'])
        after_case = next(case for case in edited if case['id'] == change['case_id'])
        after = copy.deepcopy(after_case[change['group']][change['dimension']])
        audit.append({'sequence': index, 'case_id': change['case_id'],
                      'group': change['group'], 'dimension': change['dimension'],
                      'before': before, 'after': after})
    return edited, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path,
                        default=Path(__file__).parent / 'data/case_records.json')
    parser.add_argument('--draft', type=Path, required=True,
                        help='Strict JSON list of synthetic rating changes')
    parser.add_argument('--output', type=Path, required=True,
                        help='New case-record file; existing paths are never replaced')
    parser.add_argument('--confirm', action='store_true',
                        help='Export only after reviewing the printed change list')
    args = parser.parse_args()
    try:
        cases = load_cases(args.input)
        edited, audit = apply_draft(cases, load_json(args.draft))
        print(json.dumps({'notice': ('Synthetic draft only; evidence truth and scoring '
                                    'conventions remain unvalidated.'),
                          'changes': audit}, indent=2, ensure_ascii=False))
        if not args.confirm:
            print('Preview only; no file was written. Re-run with --confirm to export.')
            return
        export_cases(edited, args.output)
        print(f'Exported {len(audit)} validated changes to {args.output}.')
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
