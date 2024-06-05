# Use a Python base image
FROM python:3.10.11

# Set the working directory
WORKDIR /airflow

# Copy the requirements file
COPY requirements.txt .

# Install the required packages
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY airflow /airflow

# Set to home directory
WORKDIR ${AIRFLOW_HOME}

# UI
EXPOSE 8080

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/entrypoint"]
CMD ["--help"]