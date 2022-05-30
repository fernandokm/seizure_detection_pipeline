# InfluxDB env vars
export INFLUXDB_HOST_URL=influxdb
export INFLUXDB_USERNAME=admin
export INFLUXDB_PASSWORD=wdkjsdk8hcjbw
export INFLUXDB_DATABASE=visualizations

# Grafana env vars
export GRAFANA_USERNAME=admin
export GRAFANA_PASSWORD=admin
export POSTGRES_DATABASE_GRAFANA=grafana

# PostgreSQL env vars
export POSTGRES_HOST_URL=postgres
export POSTGRES_DATABASE=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=wdkjsdk8hcjbw
export POSTGRES_LOCALHOST=localhost

# Airflow env vars
export POSTGRES_DATABASE_AIRFLOW=airflow

# MLFlow env vars
export POSTGRES_DATABASE_MLFLOW=mlflow

# IDs
export AIRFLOW_UID=$(id -u)
export AIRFLOW_GID=$(id -g)

# Ports
export POSTGRES_PORT=5432
export INFLUXDB_PORT=8086
export AIRFLOW_PORT=8080
export GRAFANA_PORT=3000
export MLFLOW_PORT=6000
export GE_PORT=8082
export REDIS_PORT=6379
export FLOWER_PORT=5555

# DATA PATH
export DATA_PATH='./data'
export SYMLINK_FOLDER='test_airflow'
