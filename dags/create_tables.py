# Imports
import airflow
from datetime import timedelta, datetime
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

# Arguments
default_args = {
        'owner': 'Matheus',
        'depends_on_past': False,
        'start_date': datetime(2024, 6, 4),
        'retries': 1,
        'retry_delay': timedelta(minutes=2),
        }

# Queries to create tables
query_create_tb_directions = """
CREATE TABLE IF NOT EXISTS tb_directions 
(Travel_distance integer NOT NULL,
 Travel_duration integer NOT NULL,
 Destination VARCHAR(300) NOT NULL,
 Origin VARCHAR(300) NOT NULL,
 Summary_highway VARCHAR(250) NOT NULL,
 Time timestamp without time zone NOT NULL
 );
 """

query_create_tb_weather = """
CREATE TABLE IF NOT EXISTS tb_weather 
(Description VARCHAR(250) NOT NULL,
 Temperature double precision NOT NULL,
 Humidity integer NOT NULL,
 Wind_Speed double precision NOT NULL,
 Time timestamp without time zone NOT NULL,
 Clouds integer NOT NULL,
 Location VARCHAR(250) NOT NULL
 );
 """

# DAG
dag_postgres = DAG(dag_id = "create_tables",
                   default_args = default_args,
                   schedule_interval = '@once',  
                   dagrun_timeout = timedelta(minutes = 10),
                   description = 'Criacao das tabelas no banco PostgreSQL',
)

# Instruction to create table 'tb_directions'
create_tb_directions = PostgresOperator(sql = query_create_tb_directions,
                               task_id = "task_create_tb_directions",
                               postgres_conn_id = "postgres_conn",
                               dag = dag_postgres
)

# Instruction to create table 'tb_weather'
create_tb_weather = PostgresOperator(sql = query_create_tb_weather,
                               task_id = "task_create_tb_weather",
                               postgres_conn_id = "postgres_conn",
                               dag = dag_postgres
)

# Flow
create_tb_directions >> create_tb_weather

# Main - execute dag
if __name__ == "__main__":
    dag_postgres.cli()