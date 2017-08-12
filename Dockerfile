# Dockerfile for celery workers
FROM continuumio/miniconda3


RUN mkdir -p /app

# Copy the requirements file so we can install deps. in the container
COPY requirements_dev.txt /app/
COPY requirements.txt /app/
COPY create_anuga_env.sh /app/

# Install any needed packages specified in requirements.txt
RUN pip install -r /app/requirements_dev.txt

# Create the anuga environment
RUN chmod +x /app/create_anuga_env.sh
RUN [ "/bin/bash", "-c", "/app/create_anuga_env.sh" ]


# Set the working directory to /app
WORKDIR /app
COPY . /app

# Run app.py when the container launches
# Note - a redis container is required
CMD ["celery", "-A",  "qflow",  "worker", "-l", "info", "-Ofair"]
