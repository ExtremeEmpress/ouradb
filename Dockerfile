FROM debian:bookworm-slim

WORKDIR /root

RUN apt update 
RUN apt upgrade -y 
RUN apt install -y apt-utils ca-certificates curl htop libfontconfig vim net-tools supervisor wget gnupg python3 python3-pip nodejs cron anacron procps

#Setup Supervisord
RUN mkdir -p /var/log/supervisor 
RUN mkdir -p /etc/supervisor/conf.d
COPY etc/supervisord/services.conf /etc/supervisor/conf.d/

# Configure Oura API script
RUN pip3 install influxdb-client requests --break-system-packages
COPY etc/oura/* /etc/oura/
RUN chmod +x /etc/oura/oura_post_to_influxdb.py
RUN chmod +x /etc/oura/oura_query.py


# Configure cron to query for new data
COPY etc/cron.hourly/oura_post /etc/cron.hourly/
RUN chmod +x /etc/cron.hourly/oura_post

#Cleanup
RUN apt clean
RUN rm -rf /var/lib/apt/lists/*

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]