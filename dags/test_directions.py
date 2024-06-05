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

def load_data(task_instance):
    data = task_instance.xcom_pull(task_ids="extract_directions_data")
    distance = data["routes"][0]['legs'][0]["distance"]["value"]
    duration = data["routes"][0]['legs'][0]["duration"]["value"]
    destination = data["routes"][0]['legs'][0]["end_address"]
    origin = data["routes"][0]['legs'][0]["start_address"]
    traffic_speed = data["routes"][0]['legs'][0]["traffic_speed_entry"]
    summary_highway = data["routes"][0]["summary"]
    now = datetime.now()

    loaded_data = {
                   "Travel_distance": distance,
                   "Travel_duration": duration,
                   "Destination": destination,
                   "Origin": origin,
                   "Traffic_speed": traffic_speed,
                   "Summary_highway": summary_highway,
                   "Time": now.strftime("%d%m%Y%H%M%S")
                   }
    
    loaded_list = [loaded_data]
    df_data = pd.DataFrame(loaded_list)
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = 'directions_test_' + dt_string
    df_data.to_csv(f"dags/{dt_string}.csv", index=False)

# Argumentos
default_args = {
        'owner': 'Matheus',
        'depends_on_past': False,
        'start_date': datetime(2024, 5, 24),
        'retries': 1,
        'retry_delay': timedelta(minutes=1)
        }

with DAG(dag_id = "test_directions",
                   default_args = default_args,
                   # schedule_interval='0 0 * * *',
                   schedule_interval = '@once',  
                   dagrun_timeout = timedelta(minutes = 10),
                   description = 'Job ETL de extracao de dados da Directions API'
) as dag:
    directions_api_ready = HttpSensor(
        task_id ='directions_api_ready',
        http_conn_id='directions_api',
        endpoint='/maps/api/directions/json?destination=Brasilia&origin=Juiz-de-fora&key=YOUR_API_KEY'
    )
    
    extract_directions_data = SimpleHttpOperator(
        task_id = 'extract_directions_data',
        http_conn_id = 'directions_api',
        endpoint='/maps/api/directions/json?destination=Brasilia&origin=Juiz-de-fora&key=YOUR_API_KEY',
        method = 'GET',
        response_filter= lambda r: json.loads(r.text),
        log_response=True
    )

    load_directions_data = PythonOperator(
        task_id= 'load_directions_data',
        python_callable=load_data,
        provide_context=True
    )

    directions_api_ready >> extract_directions_data >> load_directions_data