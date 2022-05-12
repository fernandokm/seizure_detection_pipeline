import argparse
import os
import sys
import pickle
from typing import List

import numpy as np
import pandas as pd


sys.path.append('.')
from src.usecase.utilities import convert_args_to_dict
from src.usecase.compute_hrvanalysis_features import FEATURES_KEY_TO_INDEX


def generate_predictions(model,
                         cons_file: str,
                         output_folder: str = 'output/preds-v0_6'):
    os.makedirs(output_folder, exist_ok=True)
    df = pd.read_csv(cons_file)
    df['predicted_label'] = np.nan

    if model is not None:
        x = df[list(FEATURES_KEY_TO_INDEX.keys())]
        notna = ~(x.isna().any(axis=1) | np.isinf(x).any(axis=1))
        if notna.any():
            df.loc[notna, 'predicted_label'] = model.predict(x[notna])
    output_file = os.path.join(output_folder, os.path.basename(cons_file))
    df.to_csv(output_file, index=False)
    return output_file


def generate_predictions_cli(model_path: str,
                             cons_file: str,
                             output_folder: str = 'output/preds-v0_6'):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    if hasattr(model, 'best_estimator_'):
        model = model.best_estimator_
    return generate_predictions(model, cons_file, output_folder)


def parse_generate_prediction_args(
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
    parser.add_argument('cons_file')
    parser.add_argument('--model-path', default='ml_model.pkl',
                        dest='model_path')
    parser.add_argument('--output-folder',
                        dest='output_folder')
    args = parser.parse_args(args_to_parse)

    return args


if __name__ == '__main__':
    args = parse_generate_prediction_args(sys.argv[1:])
    args_dict = convert_args_to_dict(args)
    generate_predictions_cli(**args_dict)
