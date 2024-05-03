FROM bikenow.vkw.tu-dresden.de/priobike/priobike-nginx:v1.0

ENV WORKER=false

# Install pip
RUN apt-get update && apt-get install -y python3-pip

# Install vi
RUN apt-get install -y vim

# Install cron and crontab
RUN apt-get install -y cron

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Set timezone to Berlin
RUN ln -snf /usr/share/zoneinfo/Europe/Berlin /etc/localtime && echo Europe/Berlin > /etc/timezone

# Make cronjobs
RUN crontab -l | { cat; echo "0 * * * * python3 /app/fetch-traffic-data.py" ; } | crontab -
RUN crontab -l | { cat; echo "1 * * * * python3 /app/predict-traffic.py /usr/share/nginx/html/prediction.json"; } | crontab - 

# Expose port 80
EXPOSE 80

# Run cron in the background
CMD python3 /app/fetch-traffic-data.py && python3 /app/predict-traffic.py /usr/share/nginx/html/prediction.json && cron && nginx -g "daemon off;"