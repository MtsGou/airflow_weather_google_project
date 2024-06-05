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
    data = [None] * 2
    data[0] = task_instance.xcom_pull(task_ids="extract_weather_data_origin")
    data[1] = task_instance.xcom_pull(task_ids="extract_weather_data_destiny")

    weather_description = [None] * 2
    temperature = [None] * 2
    humidity = [None] * 2
    wind_speed = [None] * 2
    clouds = [None] * 2
    location = [None] * 2
    time_of_record = [None] * 2

    for i in range(2):
        weather_description[i] = data[i]["weather"][0]['description']
        temperature[i] = data[i]["main"]["temp"] - 273.15 # to Celsius
        humidity[i] = data[i]["main"]["humidity"]
        wind_speed[i] = data[i]["wind"]["speed"]
        clouds[i] = data[i]["clouds"]["all"]
        location[i] = data[i]["name"]
        time_of_record[i] = datetime.utcfromtimestamp(data[i]['dt'] + data[i]['timezone'])
        loaded_data = {
            "description": weather_description[i],
            "temperature": temperature[i],
            "humidity": humidity[i],
            "wind_speed": wind_speed[i],
            "time": time_of_record[i],
            "clouds": clouds[i],
            "location": location[i]
        }
        loaded_list = [loaded_data]
        df_data = pd.DataFrame(loaded_list)
        
        #now = datetime.now()
        #dt_string = now.strftime("%d%m%Y%H%M%S")
        #dt_string = 'current_weather_data_' + location[i] + dt_string
        #df_data.to_csv(f"dags/{dt_string}.csv", index=False)

        # Get connection to postgres: id of connection created -> postgress_conn
        conn = BaseHook.get_connection('postgres_conn')
        engine = create_engine(f"postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}")
        #Load row to table in database (method None and append is to use standard SQL INSERT clause, one per row)
        df_data.to_sql("tb_weather", engine, if_exists = 'append', method=None, index = False)

# Argumentos
default_args = {
        'owner': 'Matheus',
        'depends_on_past': False,
        'start_date': datetime(2024, 5, 24),
        'retries': 3,
        'retry_delay': timedelta(minutes=1),
        }

with DAG(dag_id = "dag_ETL_weather",
                   default_args = default_args,
                   schedule_interval= '*/10 * * * *', # every 10 minutes dag
                   #schedule_interval='@once',
                   dagrun_timeout = timedelta(minutes = 5),
                   description = 'Job ETL de extracao de dados da OpenWeather'
) as dag:
    weather_api_ready_origin = HttpSensor(
        task_id ='weather_api_ready_origin',
        http_conn_id='weathermap_api',
        endpoint='/data/2.5/weather?lat=-21.78&lon=-43.34&APPID=YOUR_API_KEY'
    )
    
    extract_weather_data_origin = SimpleHttpOperator(
        task_id = 'extract_weather_data_origin',
        http_conn_id = 'weathermap_api',
        endpoint='/data/2.5/weather?lat=-21.78&lon=-43.34&APPID=YOUR_API_KEY',
        method = 'GET',
        response_filter= lambda r: json.loads(r.text),
        log_response=True
    )

    weather_api_ready_destiny = HttpSensor(
        task_id ='weather_api_ready_destiny',
        http_conn_id='weathermap_api',
        endpoint="/data/2.5/weather?q=Sao%20Paulo&appid=YOUR_API_KEY"
    )

    extract_weather_data_destiny = SimpleHttpOperator(
        task_id = 'extract_weather_data_destiny',
        http_conn_id = 'weathermap_api',
        endpoint="/data/2.5/weather?q=Sao%20Paulo&appid=YOUR_API_KEY",
        method = 'GET',
        response_filter= lambda r: json.loads(r.text),
        log_response=True
    )

    transform_load_weather_data = PythonOperator(
        task_id= 'transform_load_weather_data',
        python_callable=transform_load_data,
        provide_context=True
    )
    weather_api_ready_origin >> extract_weather_data_origin >> \
        weather_api_ready_destiny >> extract_weather_data_destiny >> transform_load_weather_data
