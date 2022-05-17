"""
This script is used to compute hrvanalysis features on RR intervals.

copyright (c) 2021 association aura
spdx-license-identifier: gpl-3.0
"""
import argparse
import os
import glob
import sys
from typing import Hashable, Iterable, Iterator, List, Tuple, Generic, TypeVar

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix


sys.path.append('.')
from src.usecase.utilities import convert_args_to_dict


T = TypeVar('T')
Interval = Tuple[int, int]

MIN_PREDICTION_OVERLAP_PERCENT = .75
MAX_OVERPREDICTION = 60


class Peekable(Generic[T]):
    EMPTY = object()

    def __init__(self, iterator: Iterator[T]):
        self.it = iterator
        self.value = self.EMPTY

    def peek(self) -> T:
        if self.value is self.EMPTY:
            self.value = next(self.it)
        return self.value  # type: ignore

    def next(self) -> T:
        val = self.peek()
        self.value = self.EMPTY
        return val

    def has_next(self) -> bool:
        try:
            self.peek()
            return True
        except StopIteration:
            return False


def identify_crises(cons_folder: str = 'output/preds-v0_6',
                    output_folder: str = 'output/crises-v0_6'):
    os.makedirs(output_folder, exist_ok=True)
    real_crises = []
    pred_crises = []
    sessions = []
    crises_intersections = []
    metrics = {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0}
    for i, cons_file in enumerate(glob.iglob(os.path.join(cons_folder, "**/*.csv"), recursive=True)):
        cons_file_name = os.path.basename(cons_file)
        patient_and_session_id = cons_file_name.replace('cons_', '').replace('.csv', '')
        patient_id, session_id = patient_and_session_id.split('_', 1)

        df = pd.read_csv(cons_file, parse_dates=['timestamp'])
        df['timestamp'] = df['timestamp'].values.astype(np.int64) / 10**9
        if 'predicted_label' not in df:
            df['predicted_label'] = np.nan
        if not is_sorted(df['interval_start_time'].to_numpy()):
            print(f'[{i}] Sorting {cons_file_name} because it\'s not already sorted')
            df.sort_values('interval_start_time')

        df_preds = df.dropna(subset=['label', 'predicted_label'])
        if not df_preds.empty:
            tn, fp, fn, tp = confusion_matrix(df_preds['label'], df_preds['predicted_label'], labels=[0, 1]).ravel()
            metrics['tn'] += tn
            metrics['fp'] += fp
            metrics['fn'] += fn
            metrics['tp'] += tp

        sessions.append({
            'patient_id': patient_id,
            'session_id': session_id,
            'cons_file': cons_file,
            'time_start': df.iloc[0]['timestamp'],
            'time_end': df.iloc[-1]['timestamp'],
        })

        def get_crisis(start: int, end: int) -> dict:
            return {
                'patient_id': patient_id,
                'session_id': session_id,
                'start': start,
                'end': end,
                'time_start': df.iloc[start]['timestamp'],
                'time_end': df.iloc[end]['timestamp'],
            }

        real_it = Peekable(iter(get_ranges(df['label'], target_val=1)))
        pred_it = Peekable(iter(get_ranges(df['predicted_label'], target_val=1)))
        real_start = real_end = pred_start = pred_end = -1
        for interval, is_real in split_and_sort_crises(real_it, pred_it):
            # add to lists
            if is_real:
                real_start, real_end = interval
                real_crises.append(get_crisis(real_start, real_end))
            else:
                pred_start, pred_end = interval
                pred_crises.append(get_crisis(pred_start, pred_end))

            # detect intersections
            if real_start == -1 or pred_start == -1:
                continue
            intersection_start = max(real_start, pred_start)
            intersection_end = min(real_end, pred_end)
            intersection_duration = intersection_end - intersection_start
            if intersection_duration >= 1:
                crises_intersections.append({
                    'real_id': len(real_crises)-1,
                    'pred_id': len(pred_crises)-1,
                    'duration_elements': intersection_duration,
                })
        print(f'[{i}] Processed {cons_file} - total stats: {len(real_crises)} real crises, {len(pred_crises)} predicted crises')

    metrics['sensitivity'] = metrics['tp'] / (metrics['tp'] + metrics['fn'])
    metrics['specitivity'] = metrics['tn'] / (metrics['tn'] + metrics['fp'])
    tagged_crises, crises_metrics = compute_metrics(real_crises, pred_crises, crises_intersections)
    metrics.update(crises_metrics)

    dicts_to_csv(real_crises, os.path.join(output_folder, 'real_crises.csv'), drop=['start', 'end'])
    dicts_to_csv(pred_crises, os.path.join(output_folder, 'pred_crises.csv'), drop=['start', 'end'])
    dicts_to_csv(crises_intersections, os.path.join(output_folder, 'intersections.csv'))
    dicts_to_csv(sessions, os.path.join(output_folder, 'sessions.csv'))
    dicts_to_csv(tagged_crises, os.path.join(output_folder, 'tagged_crises.csv'))

    metrics_df = pd.DataFrame(metrics, index=['value']).T
    metrics_df.to_csv(os.path.join(output_folder, 'metrics.csv'), index_label='metric')


def split_and_sort_crises(real_it: Peekable[Interval], pred_it: Peekable[Interval]) \
        -> Iterable[Tuple[Interval, bool]]:
    real_start = real_end = pred_start = pred_end = -1
    while real_it.has_next() or pred_it.has_next():
        if real_it.has_next() and real_end < pred_end:
            is_real = True
        elif pred_it.has_next() and pred_end < real_end:
            is_real = False
        elif real_it.has_next():
            is_real = True
        else:
            is_real = False

        if is_real:
            real_start, real_end = real_it.next()
            yield (real_start, real_end), True
        else:
            pred_start, pred_end = pred_it.next()
            for pred_start, pred_end in split_interval(pred_start, pred_end, real_start, real_end):
                yield (pred_start, pred_end), False


def split_interval(start, end, split_start, split_end) -> Iterable[Tuple[int, int]]:
    if split_start - start > MAX_OVERPREDICTION and end >= split_start:
        yield (start, split_start-1)
        start = split_start
    if end - split_end > MAX_OVERPREDICTION and start <= split_end:
        yield (start, split_end)
        yield (split_end+1, end)
    else:
        yield (start, end)


def compute_metrics(real_crises: List[dict], pred_crises: List[dict], crises_intersections: List[dict]):
    tagged_crises = []
    processed_pred_ids = set()
    crises_metrics = {metric: 0 for metric in ('crises_fp', 'crises_tp', 'crises_fn')}

    real_to_pred = {real_id: [] for real_id in range(len(real_crises))}
    for intersection in crises_intersections:
        real_to_pred[intersection['real_id']].append(intersection['pred_id'])

    for real_id, pred_ids in real_to_pred.items():
        real_start = real_crises[real_id]['start']
        real_end = real_crises[real_id]['end']
        real_length = real_end - real_start + 1

        # Compute the intersection length
        intersection_length = 0
        time_start = real_crises[real_id]['time_start']
        time_end = real_crises[real_id]['time_end']
        for pred_id in pred_ids[::]:
            pred_start = pred_crises[pred_id]['start']
            pred_end = pred_crises[pred_id]['end']
            assert real_start - pred_start <= MAX_OVERPREDICTION
            assert pred_end - real_end <= MAX_OVERPREDICTION

            intersection_length += min(pred_end, real_end) - max(pred_start, real_start) + 1
            processed_pred_ids.add(pred_id)
            time_start = min(time_start, pred_crises[pred_id]['time_start'])
            time_end = max(time_end, pred_crises[pred_id]['time_end'])

        # Detect false positive
        overlap = intersection_length / real_length
        classification = 'crises_tp' if overlap > MIN_PREDICTION_OVERLAP_PERCENT else 'crises_fn'
        crises_metrics[classification] += 1
        tagged_crises.append({
            'real_id': real_id,
            'pred_id': None,
            'time_start': time_start,
            'time_end': time_end,
            'patient_id': real_crises[real_id]['patient_id'],
            'session_id': real_crises[real_id]['session_id'],
            'overlap': overlap,
            'classification': classification,
        })

    for pred_id in range(len(pred_crises)):
        if pred_id in processed_pred_ids:
            continue
        tagged_crises.append({
            'real_id': None,
            'pred_id': pred_id,
            'time_start': pred_crises[pred_id]['time_start'],
            'time_end': pred_crises[pred_id]['time_end'],
            'patient_id': pred_crises[pred_id]['patient_id'],
            'session_id': pred_crises[pred_id]['session_id'],
            'overlap': 0.0,
            'classification': 'fp'
        })
        crises_metrics['crises_fp'] += 1

    return tagged_crises, crises_metrics


def get_ranges(iterable: Iterable, target_val) -> Iterable[Tuple[int, int]]:
    start = None
    for i, val in enumerate(iterable):
        if start is None and val == target_val:
            start = i
        elif start is not None and val != target_val:
            yield (start, i-1)
            start = None
    if start is not None:
        yield (start, i)


def is_sorted(arr: np.ndarray) -> bool:
    return np.all(arr[:-1] < arr[1:])


def dicts_to_csv(dicts: List[dict], path: str, drop: List[Hashable] = []):
    df = pd.DataFrame(dicts)
    df.drop(drop, axis=1, inplace=True)
    df.to_csv(path, index=False)


def parse_identify_crises_args(
        args_to_parse: List[str]) -> argparse.Namespace:
    """
    Parse arguments for adaptable input.

    parameters
    ----------
    args_to_parse : List[str]
        List of the element to parse. Should be sys.argv[1:] if args are
        inputed via CLI

    returns
    -------
    args : argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='CLI parameter input')
    parser.add_argument('--cons-folder',
                        dest='cons_folder')
    parser.add_argument('--output-folder',
                        dest='output_folder')
    args = parser.parse_args(args_to_parse)

    return args


if __name__ == '__main__':
    args = parse_identify_crises_args(sys.argv[1:])
    args_dict = convert_args_to_dict(args)
    identify_crises(**args_dict)
