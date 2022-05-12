import pickle
import pandas as pd
import shap


def creation_database_shap(db, model):
    model_columns = db.columns
    shap_columns = [0]*len(model_columns)
    for i in range(len(model_columns)):
        shap_columns[i] = "shap_values_"+model_columns[i]
    explainer_patient = shap.TreeExplainer(model)
    shap_values_graf = explainer_patient.shap_values(db[model_columns])
    grafana = pd.DataFrame(shap_values_graf[1], columns=shap_columns)
    return grafana


def creation_database_shap_cli(db_name, model_name, output_file):
    db = pd.read_csv(db_name)
    with open(model_name, 'rb') as f:
        model = pickle.load(f)
    if hasattr(model, 'best_estimator_'):
        model = model.best_estimator_
    grafana = creation_database_shap(db, model)
    grafana.to_csv(output_file)
