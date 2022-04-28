from datetime import datetime
import lime
from lime import lime_tabular
from typing import Dict, List, Union
import pandas as pd


def lime_explainer_to_pd_dataframe(
    exp: lime.explanation.Explanation,
    timestamp: str,
    patient_id: int,
    session_id: int,
) -> Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]:
    """
    Converts a lime barchart to a dictionnary uploadable as postgresql data

    Parameters
    ----------
    exp: lime.explanation.Explanation
        the lime explainer used to plot the barchart graph
    timestamp: str
        timestamp of the prediction, with the following format : "YYYY-MM-DD HH:MM:SS.sss"
    patient_id: int
        id of the patient who's crisis are predicted
    session_id: int
        id of the session during which the prediction was made
    table_name: str = "lime_barchart"
        name of the postgresql table in which the data is stored

    Returns
    -------
    Dict[str, List[Dict[str, Union[datetime.timestamp, int, float, str]]]]
        a dictionnary respecting the postgresql data format
    """
    df = pd.DataFrame(exp.as_list(), columns=["feature_name", "lime_coefficient"])
    df["timestamp"] = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    df["patient_id"] = patient_id
    df["session_id"] = session_id
    return df


# pd.DataFrame : 1 column par feature, 1 column shap value par feature, timestamp (str)

if __name__ == "__main__":

    from src.visualizations.postgresql import push_postgresql_data_from_pd_dataframe

    exemple_exp_as_list = [
        ("sdnn > 45.06", 0.02411322827453069),
        ("37.81 < sdsd <= 47.72", -0.010875025043483475),
        ("1.00 < nni_50 <= 3.00", -0.010813409903775757),
        ("120.00 < range_nni <= 156.00", -0.008063098295348344),
        ("Modified_csi > 752.78", -0.00746024078046046),
        ("0.05 < cvnni <= 0.06", -0.006936012779760039),
    ]

    class FalseExp:
        def __init__(self, list):
            self.list = list

        def as_list(self):
            return self.list

    exp = FalseExp(exemple_exp_as_list)
    timestamp = "2006-10-09 09:04:50.492"
    patient_id = 1234
    session_id = 5678

    df = lime_explainer_to_pd_dataframe(exp, timestamp, patient_id, session_id)

    print(df)

    push_postgresql_data_from_pd_dataframe(
        df, "localhost", "grafana", "postgres", "wdkjsdk8hcjbw", "lime_barchart"
    )
