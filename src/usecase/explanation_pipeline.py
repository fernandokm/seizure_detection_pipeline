import argparse
from typing import List
import sys
import pickle

import numpy as np
import pandas as pd
import shap
from lime import lime_tabular


sys.path.append('.')
from src.usecase.utilities import convert_args_to_dict
from src.usecase.compute_hrvanalysis_features import FEATURES_KEY_TO_INDEX


def explanation_pipeline(models, db):
    model_columns = list(FEATURES_KEY_TO_INDEX.keys())
    shap_columns = [0]*len(model_columns)
    lime_columns = [0]*len(model_columns)
    lime_table = np.full((db.shape[0], len(model_columns)), np.nan)
    for i in range(len(model_columns)):
        shap_columns[i] = "shap_values_"+model_columns[i]
        lime_columns[i] = "lime_values_"+model_columns[i]
    db.loc[:, shap_columns] = np.nan
    db.loc[:, lime_columns] = np.nan
    for model_name, model in models.items():
        x = db.loc[:, model_columns]
        row_mask = (db['model'] == model_name) & ~x.isna().any(axis=1) & ~np.isinf(x).any(axis=1)
        if not row_mask.any():
            continue
        explainer_patient = shap.TreeExplainer(model)
        shap_values_graf = explainer_patient.shap_values(db.loc[row_mask, model_columns])
        db.loc[row_mask, shap_columns] = shap_values_graf[1]
        print('Computed shap values for model', model_name)
        
        explainer_lime = lime_tabular.LimeTabularExplainer(training_data=db.loc[row_mask, model_columns].values,
                                                           mode='classification',
                                                           class_names=['no seizure', 'seizure'],
                                                           feature_names=model_columns)
        prev_label = np.nan
        prev_pred_label = np.nan
        for i in np.flatnonzero(row_mask):
            row = db.iloc[i]
            sample = row.loc[model_columns].values
            if (prev_label != 1 and row['label'] == 1) or (prev_pred_label != 1 and row['predicted_label'] == 1):
                exp = explainer_lime.explain_instance(
                    sample, model.predict_proba, labels=(0, 1), num_features=len(model_columns), num_samples=2000)
                for j in range(len(model_columns)):
                    lime_table[i, j] = exp.as_list()[j][1]
            prev_label = row['label']
            prev_pred_label = row['predicted_label']
        print('Computed lime explanation for model', model_name)
    db.loc[:, lime_columns] = lime_table


def explanation_pipeline_cli(model_name, db_name, output_file):
    db = pd.read_csv(db_name)
    with open(model_name, 'rb') as f:
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
                        dest='db_name')
    parser.add_argument('--model-name',
                        dest='model_name')
    parser.add_argument('--output-file',
                        dest='output_file')
    args = parser.parse_args(args_to_parse)

    return args


if __name__ == '__main__':
    args = parse_explanation_pipeline_args(sys.argv[1:])
    args_dict = convert_args_to_dict(args)
    explanation_pipeline_cli(**args_dict)
