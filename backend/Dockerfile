FROM python:3.8.10

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY setup.py /usr/src/app
COPY README.md /usr/src/app
COPY Rockwell.egg-info /usr/src/app
COPY src /usr/src/app/src
RUN pip install -e .

RUN apt-get update && apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor

COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY backend.conf /etc/supervisor/conf.d/backend.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"] 
