import os
from typing import Callable, Dict, List
from datetime import datetime
import logging

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
import sys
sys.path.append('.')

# from src.usecase.create_ml_dataset import ML_DATASET_OUTPUT_FOLDER, create_ml_dataset
# from src.usecase.apply_ecg_qc import apply_ecg_qc
# from src.usecase.remove_noisy_segments import remove_noisy_segments
# from src.usecase.ecg_qc_statistical_analysis import ecg_qc_statistical_analysis

START_DATE = datetime(2021, 4, 22)
CONCURRENCY = 4
SCHEDULE_INTERVAL = None
DEFAULT_ARGS = {'owner': 'airflow'}

# TO IMPORT DIRECTLY?
OUTPUT_FOLDER = 'output'

FETCHED_DATA_FOLDER = '/'.join([OUTPUT_FOLDER, 'fetched_data'])
RR_INTERVALS_FOLDER = '/'.join([OUTPUT_FOLDER, 'res-v0_6'])
FEATURES_FOLDER = '/'.join([OUTPUT_FOLDER, 'feats-v0_6'])
CONSOLIDATED_FOLDER = '/'.join([OUTPUT_FOLDER, 'cons-v0_6'])
PREDICTIONS_FOLDER = '/'.join([OUTPUT_FOLDER, 'preds-v0_6'])
CRISES_FOLDER = '/'.join([OUTPUT_FOLDER, 'crises-v0_6'])
DEFAULT_MODEL_FOLDER = 'pipeline_models'
# DICT_PARAMS_EDF_FILE = {
#     "patient": "PAT_6",
#     "record": "77",
#     "file_path": "",
#     "segment": "s1",
#     "channel_name": "emg6+emg6-",
#     "start_time": "2020-12-18 13:00:00",
#     "end_time": "2020-12-18 14:30:00",
#     "data_path": 'data'
# }
# INFOS = list(DICT_PARAMS_EDF_FILE.values())[:4]

DETECT_QRS_METHOD = 'hamilton'
ECG_QC_MODEL = 'rfc_normalized_2s.pkl'
LENGTH_CHUNK = 2

SLIDING_WINDOW = 1_000
SHORT_WINDOW = 10_000
MEDIUM_WINDOW = 60_000
LARGE_WINDOW = 150_000

NUM_PARTITIONS = 8

SEGMENT_SIZE_TRESHOLD = 0.9

AIRFLOW_PREFIX_TO_DATA = '/opt/airflow/'


def map_parameters(fn: Callable, parameters_list: list) -> list:
    """Similar to `list(map(fn, parameters))`, but with error checking and logging.
    """
    results = []
    total = len(parameters_list)
    for i, parameters in enumerate(parameters_list):
        if parameters is None:
            logging.info(f'Skipping item {i+1}/{total}: failed on previous subtask')
            continue
        try:
            results.append(fn(parameters))
            logging.info(f'Processed item {i+1}/{total}')
        except Exception as err:
            logging.error(f'Error processing item {i+1}/{total}: {err}')
            results.append(None)
    return results


@dag(default_args=DEFAULT_ARGS,
     dag_id='seizure_detection_pipeline',
     description='Start the whole seizure detection pipeline',
     start_date=START_DATE,
     schedule_interval=SCHEDULE_INTERVAL,
     concurrency=CONCURRENCY)
def dag_seizure_detection_pipeline():

    @task()
    def t_detect_qrs(parameters_list: List[dict]) -> List[dict]:
        from src.usecase.detect_qrs import detect_qrs

        def inner(parameters: dict):
            output_qrs_file_path, sampling_frequency = detect_qrs(
                qrs_file_path=parameters['qrs_file_path'],
                exam_id=parameters['exam_id'],
                method=parameters['method'],
                output_folder=parameters['rr_intervals_folder'])

            output_parameters = {'rr_file_path': output_qrs_file_path,
                                 'sampling_frequency': sampling_frequency}

            return output_parameters

        return map_parameters(inner, parameters_list)

    @task()
    def t_consolidate_parameters(param_dict_1_list: List[dict],
                                 param_dict_2_list: List[dict]) -> List[dict]:
        consolidated_parameters_list = []
        for param_dict_1, param_dict_2 in zip(param_dict_1_list, param_dict_2_list):
            if param_dict_1 is None or param_dict_2 is None:
                consolidated_parameters_list.append(None)
            else:
                consolidated_parameters_list.append({**param_dict_1, **param_dict_2})

        return consolidated_parameters_list

    @task()
    def t_compute_hrv_analysis_features(parameters_list: List[dict]) -> List[dict]:
        from src.usecase.compute_hrvanalysis_features import compute_hrvanalysis_features

        def inner(parameters: dict) -> dict:
            output_features_file_path = compute_hrvanalysis_features(
                rr_intervals_file_path=parameters['rr_file_path'],
                output_folder=parameters['features_folder'],
                sliding_window=SLIDING_WINDOW,
                short_window=SHORT_WINDOW,
                medium_window=MEDIUM_WINDOW,
                large_window=LARGE_WINDOW)

            output_parameters = {
                'features_file_path': output_features_file_path}

            return output_parameters

        return map_parameters(inner, parameters_list)

    @task()
    def t_compute_consolidate_feats_and_annot(parameters_list: List[dict]) -> List[dict]:
        from src.usecase.consolidate_feats_and_annot import consolidate_feats_and_annot, WINDOW_INTERVAL

        def inner(parameters: dict) -> dict:
            output_cons_file_path = consolidate_feats_and_annot(
                features_file_path=parameters['features_file_path'],
                annotations_file_path=parameters['annotations_file_path'],
                output_folder=parameters['consolidated_folder'],
                window_interval=WINDOW_INTERVAL,
                segment_size_treshold=SEGMENT_SIZE_TRESHOLD,
                crop_dataset=True)

            output_parameters = {
                'cons_file_path': output_cons_file_path}

            return output_parameters

        return map_parameters(inner, parameters_list)

#    @task(depends_on_past=True, trigger_rule=TriggerRule.ALL_DONE)
#    def t_create_ml_dataset():
#        create_ml_dataset(
#            input_folder=CONSOLIDATED_FOLDER,
#            output_folder=ML_DATASET_OUTPUT_FOLDER)
#
#
#     @task()
#     def t_apply_ecg_qc(filepath: str,
#                        output_folder: str,
#                        sampling_frequency: int,
#                        model: str,
#                        exam_id: str) -> str:
#
#         filename = apply_ecg_qc(filepath,
#                                 output_folder,
#                                 sampling_frequency,
#                                 model,
#                                 exam_id)
#
#         return filename # rename
#
#     @task()
#     def t_remove_noisy_segment(rr_intervals_file,
#                                chunk_file,
#                                length_chunk,
#                                sampling_frequency) -> str:
#
#         filename = remove_noisy_segments(rr_intervals_file,
#                                          chunk_file,
#                                          length_chunk,
#                                          sampling_frequency)
#
#         return filename
#
#     @task()
#     def t_ecg_qc_statistical_analysis(chunk_file: str) -> str:
#         ecg_qc_statistical_analysis(chunk_file)
#
#    db_list_filename = t_fetch_database(
#        {
#            "data_folder_path": "data/tuh",
#            "export_folder": "output/db"
#        }
#    )

    @task()
    def t_get_initial_parameters(partition_index: int) -> List[dict]:
        import pandas as pd
        # Split the df_db into blocks df_db[0:partition_size], df_db[partition_size:2*partition_size], ...
        df_db = pd.read_csv(f'{FETCHED_DATA_FOLDER}/df_candidates.csv', encoding='utf-8')
        partition_size = (df_db.shape[0] + NUM_PARTITIONS - 1) // NUM_PARTITIONS
        partition_start = partition_index * partition_size
        partition_end = (partition_index+1) * partition_size
        df_db = df_db.iloc[partition_start:partition_end]

        parameters_list = []
        for index in range(df_db.shape[0]):
            qrs_file_path = df_db['edf_file_path'].iloc[index]
            tse_bi_file_path = df_db['annotations_file_path'].iloc[index]
            exam_id = df_db['exam_id'].iloc[index]
            parameters = {'qrs_file_path': ''.join([AIRFLOW_PREFIX_TO_DATA,
                                                    qrs_file_path]),
                          'annotations_file_path': ''.join([AIRFLOW_PREFIX_TO_DATA,
                                                            tse_bi_file_path]),
                          'exam_id': exam_id,
                          'method': DETECT_QRS_METHOD,
                          'rr_intervals_folder': RR_INTERVALS_FOLDER,
                          'features_folder': FEATURES_FOLDER,
                          'consolidated_folder': CONSOLIDATED_FOLDER}
            parameters_list.append(parameters)
        return parameters_list

    for partition_index in range(NUM_PARTITIONS):
        parameters_list = t_get_initial_parameters(partition_index)

        qrs_parameters_list = t_detect_qrs(parameters_list)
        parameters_list = t_consolidate_parameters(parameters_list,
                                                   qrs_parameters_list)

        features_parameters_list = t_compute_hrv_analysis_features(parameters_list)
        parameters_list = t_consolidate_parameters(parameters_list,
                                                   features_parameters_list)

        consolidated_feats_and_annot_parameters_list = \
            t_compute_consolidate_feats_and_annot(parameters_list)
        parameters_list = t_consolidate_parameters(
            parameters_list,
            consolidated_feats_and_annot_parameters_list)


#        file_quality = t_apply_ecg_qc(filepath=data_file_path,
#                                      output_folder=OUTPUT_FOLDER,
#                                      sampling_frequency=SAMPLING_FREQUENCY,
#                                      model=ECG_QC_MODEL,
#                                      exam_id=exam_id)
#
#        file_clean_rr_intervals = t_remove_noisy_segment(
#            rr_intervals_file=file_rr_intervals,
#            chunk_file=file_quality,
#            length_chunk=LENGTH_CHUNK,
#            sampling_frequency=sampling_frequency)
#
        # t_ecg_qc_statistical_analysis(chunk_file=file_quality)


@dag(default_args={
        'model_paths': {},
        **DEFAULT_ARGS,
     },
     dag_id='model_pipeline',
     description='Start the whole seizure detection pipeline',
     start_date=START_DATE,
     schedule_interval=SCHEDULE_INTERVAL,
     concurrency=CONCURRENCY)
def dag_model_pipeline():
    def load_models(model_paths: dict):
        import pickle
        models = {}
        for model_name, model_path in model_paths.items():
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                if hasattr(model, 'best_estimator_'):
                    model = model.best_estimator_
                models[model_name] = model
            except Exception as err:
                raise RuntimeError(f'Cannot generate predictions for model {model_name} at {model_path}') from err
        return models

    @task()
    def t_get_initial_parameters(partition_index: int) -> List[dict]:
        import pandas as pd
        import os
        from os import path
        # Split the df_db into blocks df_db[0:partition_size], df_db[partition_size:2*partition_size], ...
        df_db = pd.read_csv(f'{FETCHED_DATA_FOLDER}/df_candidates.csv', encoding='utf-8')
        partition_size = (df_db.shape[0] + NUM_PARTITIONS - 1) // NUM_PARTITIONS
        partition_start = partition_index * partition_size
        partition_end = (partition_index+1) * partition_size
        print('Running partition', partition_index, '(rows', partition_start, 'to', partition_end-1, ')')
        df_db = df_db.iloc[partition_start:partition_end]

        model_paths = get_current_context()['params'].get('model_paths', {})
        if not model_paths:
            print('No models specified, loading all available models')
            for file in os.listdir(DEFAULT_MODEL_FOLDER):
                if file.lower().endswith('.pkl'):
                    model_name = file[:-4]
                    model_path = os.path.join(DEFAULT_MODEL_FOLDER, file)
                    model_paths[model_name] = model_path
            print('Running with models:', model_paths)

        cons_files = os.listdir(CONSOLIDATED_FOLDER)
        parameters_list = []
        for index in range(df_db.shape[0]):
            qrs_file_path = df_db['edf_file_path'].iloc[index]
            session, _ = path.splitext(path.basename(qrs_file_path))

            matches = [f for f in cons_files if session in f]
            if matches:
                cons_file_path = matches[0]
                print('Found cons file', cons_file_path)
            else:
                print('No cons file for session', session)
                continue

            parameters = {'cons_file_path': path.join(CONSOLIDATED_FOLDER, cons_file_path),
                          'consolidated_folder': CONSOLIDATED_FOLDER,
                          'predictions_folder': PREDICTIONS_FOLDER,
                          'crises_folder': CRISES_FOLDER,
                          'model_paths': model_paths}
            parameters_list.append(parameters)
        return parameters_list

    @task()
    def t_generate_predictions_and_shap(parameters_list: List[dict]) -> List[dict]:
        if not parameters_list:
            return []

        from src.usecase.generate_predictions import generate_predictions
        from src.usecase.explanation_pipeline import explanation_pipeline
        import pandas as pd
        models = load_models(parameters_list[0]['model_paths'])

        def inner(parameters: dict) -> dict:
            predictions_file_path = os.path.join(
                parameters['predictions_folder'],
                os.path.basename(parameters['cons_file_path']),
            )
            os.makedirs(parameters['predictions_folder'], exist_ok=True)
            df = pd.read_csv(parameters['cons_file_path'])
            df = generate_predictions(models, df)
            print('Generated predictions')
            explanation_pipeline(models, df)
            print('Generated explanations')
            df.to_csv(predictions_file_path, index=False)
            return {
                'predictions_file_path': predictions_file_path
            }
        return map_parameters(inner, parameters_list)

    @task()
    def t_identify_crises(parameters_list: List[List[dict]]) -> None:
        from src.usecase.identify_crises import identify_crises
        identify_crises(PREDICTIONS_FOLDER, CRISES_FOLDER)

    output_parameters = []
    for partition_index in range(NUM_PARTITIONS):
        parameters_list = t_get_initial_parameters(partition_index)
        parameters_list = t_generate_predictions_and_shap(parameters_list)
        output_parameters.append(parameters_list)

    t_identify_crises(output_parameters)


@dag(default_args=DEFAULT_ARGS,
     dag_id='grafana_pipeline',
     description='Start the grafana pipeline',
     start_date=START_DATE,
     schedule_interval=SCHEDULE_INTERVAL,
     concurrency=CONCURRENCY)
def dag_grafana_pipeline():
    @task()
    def t_get_initial_parameters() -> dict:
        import pandas as pd
        import os
        from os import path

        parameters = {
            'edf_sources': {},
            'csv_sources': {},
            'csv_crises': {
                "crises": path.join(CRISES_FOLDER, "crises.csv"),
                "metrics": path.join(CRISES_FOLDER, "metrics.csv"),
                "intersections": path.join(CRISES_FOLDER, "intersections.csv"),
                "sessions": path.join(CRISES_FOLDER, "sessions.csv"),
                "tagged_crises": path.join(CRISES_FOLDER, "tagged_crises.csv"),
            },
        }

        preds_files = [os.path.join(PREDICTIONS_FOLDER, file) for file in os.listdir(PREDICTIONS_FOLDER)]
        df_db = pd.read_csv(f'{FETCHED_DATA_FOLDER}/df_candidates.csv', encoding='utf-8')
        for _, row in df_db.iterrows():
            edf_file_path = row['edf_file_path']
            session, _ = path.splitext(path.basename(edf_file_path))
            parameters["edf_sources"][session] = edf_file_path

            matches = [f for f in preds_files if session in f]
            if matches:
                parameters["csv_sources"][session] = matches[0]
                print('Found preds file', matches[0])
            else:
                print('No preds file for session', session)
                continue

        return parameters

    @task()
    def t_generate_postgresql_data(parameters: dict) -> None:
        from src.visualizations.generate_data import generate_postgresql_data
        generate_postgresql_data({**parameters["csv_crises"], **parameters["csv_sources"]})

    @task()
    def t_generate_influxdb_data(parameters: dict) -> None:
        from src.visualizations.generate_data import generate_influxdb_data
        generate_influxdb_data(edf_files=parameters["edf_sources"], csv_files={})

    parameters = t_get_initial_parameters()
    t_generate_postgresql_data(parameters)
    t_generate_influxdb_data(parameters)


dag_pipeline = dag_seizure_detection_pipeline()
model_pipeline = dag_model_pipeline()
grafana_pipeline = dag_grafana_pipeline()
