# Imports
import airflow
from airflow import DAG
from datetime import timedelta, datetime
from airflow.utils.dates import days_ago
from airflow.providers.http.sensors.http import HttpSensor
import json
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from airflow.hooks.base import BaseHook
from sqlalchemy import create_engine

def transform_load_data(task_instance):
    data = task_instance.xcom_pull(task_ids="extract_directions_data")

    # Distance in meters
    distance = data["routes"][0]['legs'][0]["distance"]["value"]

    # Duration in seconds
    duration = data["routes"][0]['legs'][0]["duration"]["value"]

    # Convert duration to minutes
    duration = int(duration/60)

    destination = data["routes"][0]['legs'][0]["end_address"]
    origin = data["routes"][0]['legs'][0]["start_address"]
    summary_highway = data["routes"][0]["summary"]

    # Correct time zone
    now = datetime.now() - timedelta(hours=3, minutes=0)

    loaded_data = {
                   "travel_distance": distance,
                   "travel_duration": duration,
                   "destination": destination,
                   "origin": origin,
                   "summary_highway": summary_highway,
                   "time": now.strftime("%Y-%m-%d %H:%M:%S")
                   }
    
    loaded_list = [loaded_data]
    df_data = pd.DataFrame(loaded_list)
    #dt_string = now.strftime("%d%m%Y%H%M%S")
    #dt_string = 'directions_test_' + dt_string
    #df_data.to_csv(f"dags/{dt_string}.csv", index=False)

    # Get connection to postgres: id of connection created -> postgress_conn
    conn = BaseHook.get_connection('postgres_conn')
    engine = create_engine(f"postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}")
    #Load row to table in database (method None and append is to use standard SQL INSERT clause, one per row)
    df_data.to_sql("tb_directions", engine, if_exists = 'append', method=None, index = False)
    



# Argumentos
default_args = {
        'owner': 'Matheus',
        'depends_on_past': False,
        'start_date': datetime(2024, 5, 29),
        'retries': 3,
        'retry_delay': timedelta(minutes=2),
        }

with DAG(dag_id = "dag_ETL_directions",
                   default_args = default_args,
                   schedule_interval= '*/10 * * * *', # every 10 minutes dag
                   #schedule_interval='@once',
                   dagrun_timeout = timedelta(minutes = 10),
                   description = 'Job ETL de extracao de dados da Directions API'
) as dag:
    directions_api_ready = HttpSensor(
        task_id ='directions_api_ready',
        http_conn_id='directions_api',
        endpoint="/maps/api/directions/json?destination=Sao-Paulo&origin=Juiz-de-fora&key=YOUR_API_KEY"
    )
    
    extract_directions_data = SimpleHttpOperator(
        task_id = 'extract_directions_data',
        http_conn_id = 'directions_api',
        endpoint="/maps/api/directions/json?destination=Sao-Paulo&origin=Juiz-de-fora&key=YOUR_API_KEY",
        method = 'GET',
        response_filter= lambda r: json.loads(r.text),
        log_response=True
    )

    transform_load_directions_data = PythonOperator(
        task_id= 'transform_load_directions_data',
        python_callable=transform_load_data,
        provide_context=True
    )

    directions_api_ready >> extract_directions_data >> transform_load_directions_data