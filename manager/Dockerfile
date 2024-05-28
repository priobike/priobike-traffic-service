FROM bikenow.vkw.tu-dresden.de/priobike/priobike-nginx:v1.0

# Install pip
RUN apt-get update && apt-get install -y python3-pip

# Install cron and crontab
RUN apt-get install -y cron procps

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Set timezone to Berlin
RUN ln -snf /usr/share/zoneinfo/Europe/Berlin /etc/localtime && echo Europe/Berlin > /etc/timezone

# Expose port 80
EXPOSE 80

CMD /app/start.sh