FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y curl build-essential libssl-dev \
    && apt-get clean

RUN pip3 install poetry

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false
RUN poetry check
RUN poetry install --no-root --no-interaction --no-ansi

COPY src/ /app/src/
COPY sample_posts.json /app/ 

ENV PYTHONPATH=/app/src

EXPOSE 8000

# Run Uvicorn
CMD ["poetry", "run", "uvicorn", "rockwell.main:app", "--host", "0.0.0.0", "--port", "8000"]
