# Explainability Pipeline

The explainability pipeline aims to explain why the machine learning model predicted (or not) a given seizure.

## Technical documentation

For information on the design and implementation of the pipeline, as well as descriptions of all the dashboards and graphs, see the [**technical documentation**](Technical%20Documentation.md).

## Prerequisites

Similar to the main project (described [here](../README.md)), this pipeline requires:

- [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)
- the python packages listed in the [requirements.txt](../requirements.txt), which can be installed with the following command:

    ```sh
    pip install -r requirements.txt
    ```

## Getting started

First, follow the [Getting started](../README.md#Getting%20started) section of the main project using docker-compose. Once airflow is accessible, you will find three pipelines:

1. `seizure_detection_pipeline` - this is the pre-existing pipeline, which performs feature extraction
2. `model_pipeline` - this pipeline computes the explanation data using Lime and SHAP, as well as the model predictions
3. `grafana_pipeline` - this pipeline prepares the data to be used by Grafana.

Before executing the pipelines, an ML model file (in pkl format) should be placed in the `pipeline_models` directory (note that the directory must contain a single model, as support for multiple models is not implemented). The pipelines should then be executed in the order listed above.

Once all pipelines have been executed, the Grafana dashboards can be accessed on [http://localhost:3000](http://localhost:3000).
