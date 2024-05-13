FROM bikenow.vkw.tu-dresden.de/priobike/priobike-nginx:v1.0

WORKDIR /app

RUN mkdir /app/data

RUN chown -R nginx:nginx /app/data

# Install httpd-tools for htpasswd
RUN apt-get update && apt-get install -y apache2-utils

# Install curl
RUN apt-get install -y curl

COPY ./default.conf /etc/nginx/conf.d/default.conf

COPY ./init_fetch.sh /app/init_fetch.sh
RUN chmod +x /app/init_fetch.sh

# Create htpasswd file and start nginx
CMD htpasswd -bc /etc/nginx/.htpasswd $BASIC_AUTH_USER $BASIC_AUTH_PASS && /app/init_fetch.sh && nginx -g 'daemon off;'