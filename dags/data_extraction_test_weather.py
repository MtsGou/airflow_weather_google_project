
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
    data = task_instance.xcom_pull(task_ids="extract_weather_data")
    weather_description = data["weather"][0]['description']
    temperature = data["main"]["temp"]
    min_temp = data["main"]["temp_min"]
    max_temp = data["main"]["temp_max"]
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

    loaded_data = {
                   "Description": weather_description,
                   "Temperature": temperature,
                   "Minimun Temperature": min_temp,
                   "Maximum Temperature": max_temp,
                   "Pressure": pressure,
                   "Humidty": humidity,
                   "Wind Speed": wind_speed,
                   "Time of Record": time_of_record,
                   "Sunrise (Local Time)":sunrise_time,
                   "Sunset (Local Time)": sunset_time,
                   "Clouds": clouds
                   }
    loaded_list = [loaded_data]
    df_data = pd.DataFrame(loaded_list)

    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    dt_string = 'current_weather_data_juiz_de_fora_mg' + dt_string
    df_data.to_csv(f"dags/{dt_string}.csv", index=False)

# Argumentos
default_args = {
        'owner': 'Matheus',
        'depends_on_past': False,
        'start_date': datetime(2024, 5, 24),
        'retries': 1,
        'retry_delay': timedelta(minutes=1)
        }

with DAG(dag_id = "data_extraction_test_weather",
                   default_args = default_args,
                   # schedule_interval='0 0 * * *',
                   schedule_interval = '@once',  
                   dagrun_timeout = timedelta(minutes = 10),
                   description = 'Job ETL de extracao de dados da OpenWeather'
) as dag:
    weather_api_ready = HttpSensor(
        task_id ='weather_api_ready',
        http_conn_id='weathermap_api',
        endpoint='/data/2.5/weather?lat=-21.78&lon=-43.34&APPID=YOUR_API_KEY'
    )
    
    extract_weather_data = SimpleHttpOperator(
        task_id = 'extract_weather_data',
        http_conn_id = 'weathermap_api',
        endpoint='/data/2.5/weather?lat=-21.78&lon=-43.34&APPID=YOUR_API_KEY',
        method = 'GET',
        response_filter= lambda r: json.loads(r.text),
        log_response=True
    )
    load_weather_data = PythonOperator(
        task_id= 'load_weather_data',
        python_callable=load_data,
        provide_context=True
    )
    weather_api_ready >> extract_weather_data >> load_weather_data
