import argparse
from typing import List
import sys
import pickle

import pandas as pd
import shap
from lime import lime_tabular


sys.path.append('.')
from src.usecase.utilities import convert_args_to_dict
from src.usecase.compute_hrvanalysis_features import FEATURES_KEY_TO_INDEX


def shap_pipeline(model, db):
    model_columns = list(FEATURES_KEY_TO_INDEX.keys())
    shap_columns = [0]*len(model_columns)
    lime_columns = [0]*len(model_columns)
    lime_table = np.zeros(len(model_columns), db.shape(0])
    for i in range(len(model_columns)):
        shap_columns[i] = "shap_values_"+model_columns[i]
        lime_columns[i] = "lime_values_"+model_columns[i]
    explainer_patient = shap.TreeExplainer(model)
    explainer_lime = lime_tabular.LimeTabularExplainer(training_data=db[model_colums].values, 
                                              mode='classification', 
                                              class_names=['no seizure', 'seizure'],
                                              feature_names=model_columns)
    shap_values_graf = explainer_patient.shap_values(db[model_columns])
    db[shap_columns] = shap_values_graf[1]
    for i in range(db.shape[0]):
        sample = db.iloc[[i]].values
        exp = explainer.explain_instance(sample[0], model.predict_proba, labels=(0, 1), num_features=len(model_columns))
        for j in range(len(model_columns):
            lime_table[i, j] = exp.as_list()[j][1]
     db[lime_columns] = lime_table

def shap_pipeline_cli(model_name, db_name, output_file):
    db = pd.read_csv(db_name)
    with open(model_name, 'rb') as f:
        model = pickle.load(f)
    if hasattr(model, 'best_estimator_'):
        model = model.best_estimator_
    shap_pipeline(model, db)
    db.to_csv(output_file)


def parse_shap_pipeline_args(
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
    args = parse_shap_pipeline_args(sys.argv[1:])
    args_dict = convert_args_to_dict(args)
    shap_pipeline_cli(**args_dict)
