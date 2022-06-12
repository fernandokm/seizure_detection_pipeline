"""
This script computes lime and shap explanations for model predictions.

It loads a csv file with model predictions (such as the ones
generated by the generate_predictions.py script) and a pickled model,
generates the predictions, and saves everything to the output folder.

This file can also be imported as a module and provides the
explanation_pipeline function.
"""

import argparse
from typing import List
import sys
import pickle

import numpy as np
import pandas as pd
import shap
from lime import lime_tabular


sys.path.append('.')
from src.usecase.compute_hrvanalysis_features import FEATURES_KEY_TO_INDEX
from src.usecase.utilities import convert_args_to_dict


def explanation_pipeline(models: dict, db: pd.DataFrame) -> None:
    """
    Computes lime and shap explanations for model predictions.

    For each feature FEAT, three new columns are added to db:

        shap_values_FEAT : float
            The shapley values.
        lime_string_FEAT : float
            The discretized features associated with the lime
            feature importances.
        lime_values_FEAT
            The lime feature importances.

    The dataframe is modified in-place.

    Parameters
    ----------
    models: dict
        A dictionary of model_name (str) to model. The model can be any
        sklearn-compatible model.
    df: pd.DataFrame
        The dataframe with the predictions which should be explained.
        It should have the same format as the dataframes generated by
        the generate_predictions.py script.
    """
    model_columns = list(FEATURES_KEY_TO_INDEX.keys())
    shap_columns = ['']*len(model_columns)
    lime_columns = ['']*(2*len(model_columns))
    for i in range(len(model_columns)):
        shap_columns[i] = "shap_values_"+model_columns[i]
        lime_columns[2*i] = "lime_string_"+model_columns[i]
        lime_columns[2*i+1] = "lime_values_"+model_columns[i]
    db.loc[:, shap_columns] = np.nan
    db.loc[:, lime_columns] = np.nan
    for model_name, model in models.items():
        # identify which rows in db relate to the current model
        # AND have no NaN values.
        x = db.loc[:, model_columns]
        row_mask = (db['model'] == model_name) & ~x.isna().any(axis=1) & ~np.isinf(x).any(axis=1)
        if not row_mask.any():
            continue

        # compute shap explanations
        explainer_patient = shap.TreeExplainer(model)
        shap_values_graf = explainer_patient.shap_values(db.loc[row_mask, model_columns])
        db.loc[row_mask, shap_columns] = shap_values_graf[1]
        print('Computed shap values for model', model_name)

        # compute lime explanations
        explainer_lime = lime_tabular.LimeTabularExplainer(training_data=db.loc[row_mask, model_columns].values,
                                                           mode='classification',
                                                           class_names=['no seizure', 'seizure'],
                                                           feature_names=model_columns)
        prev_label = np.nan
        prev_pred_label = np.nan
        # iterate through the relevant rows
        # (np.flatnonzero(row_mask) returns the indices of db rows
        # which pertain to the current model are are not NaN)
        for i in np.flatnonzero(row_mask):
            row = db.iloc[i]
            sample = row.loc[model_columns].values

            # Only generate an explanation if db[i] has label/predicted_label == 1 (seizure)
            # and the previous row had label/predicted label != 1 (not seizure)
            if (prev_label != 1 and row['label'] == 1) or (prev_pred_label != 1 and row['predicted_label'] == 1):
                exp = explainer_lime.explain_instance(
                    sample, model.predict_proba, labels=(0, 1), num_features=len(model_columns), num_samples=2000)
                for j, weight in exp.as_map()[1]:
                    feature_name = exp.domain_mapper.feature_names[j]
                    discretized_feature = exp.domain_mapper.discretized_feature_names[j]
                    db.loc[db.index[i], f'lime_string_{feature_name}'] = discretized_feature
                    db.loc[db.index[i], f'lime_values_{feature_name}'] = weight
            prev_label = row['label']
            prev_pred_label = row['predicted_label']
        print('Computed lime explanation for model', model_name)


def explanation_pipeline_cli(model_path: str,
                             db_name: str,
                             output_file: str):
    """
    Computes lime and shap explanations for model predictions.

    This function is a wrapper of explanation_pipeline which enables
    interaction through the command line. It loads the model and
    input data, calls generate_predictions, and saves the output.

    Parameters
    ----------
    model_path: str
        The path to a pickled sklearn-compatible model.
    db_name: str
        The path to a csv file with the data to be used.
    output_file: str
        The path where the output file should be saved.
    """
    db = pd.read_csv(db_name)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    if hasattr(model, 'best_estimator_'):
        model = model.best_estimator_
    explanation_pipeline(model, db)
    db.to_csv(output_file)


def parse_explanation_pipeline_args(
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
    parser.add_argument('--db-name',
                        dest='db_name',
                        help='The path to a csv file with the data to be used')
    parser.add_argument('--model-path',
                        dest='model_path',
                        help='The path to a pickled sklearn-compatible model')
    parser.add_argument('--output-file',
                        dest='output_file',
                        help='The path where the output file should be saved')
    args = parser.parse_args(args_to_parse)

    return args


if __name__ == '__main__':
    args = parse_explanation_pipeline_args(sys.argv[1:])
    args_dict = convert_args_to_dict(args)
    explanation_pipeline_cli(**args_dict)
