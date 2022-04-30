FROM python:3.8.10

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY setup.py /usr/src/app
COPY README.md /usr/src/app
RUN pip install -e .

ENTRYPOINT ["flask"]
CMD ["run", "--host=0.0.0.0", "--port=5000"]
