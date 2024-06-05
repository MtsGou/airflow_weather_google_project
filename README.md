# Airflow ETL Data Engineering Project
The purpose of this project is to extract relevant data from Open Weather API and Google Directions API, transform and load it into a PostgreSQL database using Apache Airflow. Airflow runs on Docker, and so does the postgreSQL database, which runs on a docker container on top of a postgres image.

You can just clone the repository and make the necessary changes to it.

First, you need to create an account on OpenWeather an create an API Key, and just as well on Google Cloud Platform, enabling Directions on your GCP project and creating an API key.

Check APIs documentation:

- [Open Weather](https://openweathermap.org/current)
- [Google Directions API](https://developers.google.com/maps/documentation/directions/overview?hl=pt-br)

## If you don't have docker:

### Ubuntu
- [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#set-up-the-repository)
- [Docker Desktop](https://docs.docker.com/desktop/install/ubuntu/)

### Windows
On Windows, use WSL2. Installation instructions [here](https://learn.microsoft.com/pt-br/windows/wsl/install).

### Test if Docker is working
```
docker run hello-world
```

# Airflow Setup
Check airflow [documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html) to run it on docker using a 'docker-compose.yaml' file.

## Create containers with docker-compose file
```
docker-compose up
```

# Workspace setup
Create a directory called 'airflow' with folders 'config', 'dags', 'logs' and 'plugins'.

# Creating Dags:
The dags should be created within the 'dags' folder.

# Weather API connection:

* Connection Id: weathermap_api
* Connection Type: HTTP
* Host: https://api.openweathermap.org
* Port: blank
* Login: blank
* Password: blank
* Extra: blank

# Google Directions API connection:

* Connection Id: directions_api
* Connection Type: HTTP
* Host: https://maps.googleapis.com
* Port: blank
* Login: blank
* Password: blank
* Extra: blank

# Setting postgreSQL on docker
Run the command below in terminal or command prompt to download the Postgres image

```
docker pull postgres
```

## Initialize the container

```
docker run --name db_routes -p 5432:5432 -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=postgres -d postgres
```

# Connection to PostgreSQL database on docker

After creating a container using a postgres image:

* Connection Id: postgres_conn
* Connection Type: Postgres
* Host: host.docker.internal
* Database: postgres (name of the database, in my case I used 'postgres')
* Login: user
* Password: password
* Port: 5432 (default port for postgreSQL container)
* Extra: blank

The dags 'test_directions' and 'data_extraction_test_weather' are programmed to only execute once, as they are connection tests to APIs.

Then, the 'create_tables' dag should be executed next, to create the tables on postgres where the data is going to be loaded.

Once the connections are created on Airflow UI and the dags are created, you can trigger then (dag_ETL...) on the UI and they will execute just as you've scheduled (in this case, in every 10 minutes).

## Stopping docker containers

```
# Check containers running
docker ps
```
You can just use 
```
docker stop $(docker ps -a -q)
```
to stop all running containers.

## Configuration of docker networks (optional)

Usually using 'host.docker.internal' on port 5432 should work, but if you are still struggling, try on your terminal:

### List Docker networks, inspect container

```
docker network ls
docker inspect db_routes
```

### Extract details about the container network

```
docker inspect db_routes -f "{{json .NetworkSettings.Networks }}"
docker ps --format '{{ .ID }} {{ .Names }} {{ json .Networks }}'
```

### Inspect Airflow network and default network

```
docker network inspect airflow_default
docker network inspection bridge
```
### Disconnecting from the bridge network
```
apt-get update
apt-get install net-tools
apt-get install iputils-ping

ifconfig
ping
docker network disconnect bridge db_routes
```

### Connect to network airflow_default
```
docker network connect airflow_default db_routes
docker network inspect airflow_default
```

On docker CLI, use ifconfig. Use the inet IP address.
