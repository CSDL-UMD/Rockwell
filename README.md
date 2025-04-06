# Rockwell

Rockwell uses the twitter authentication workflow to render a twitter like feed in order to collect information about the users interaction with their feed. It also has an attention check feature to ensure that the user is being observant of their feeds and not simply scrolling through with the intent of finishing quickly.

# Tech Stack

Rockwell uses a PostgreSQL database, a Python (FastAPI) backend managed with Poetry, and a Node/React.js frontend.

# Local Installation

## Clone the project
```sh
git clone https://github.com/CSDL-UMD/Rockwell.git 
cd Rockwell
```

## Postgress Database 

Make sure you have [PostgresSql](https://www.postgresql.org/) installed and running.

Initialize the databse and update your path.
```sh
sudo psql -d postgres -f init.sql
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/rockwell"
```

## Rockwell App

Make sure you have poetry installed
```bash
pip3 install poetry
poetry --version
```

make sure your version of poetry is up to date
```sh
pip3 install poetry --upgrade
```

install the dependencies
```bash
poetry install --no-root --no-interaction --no-ansi
```

run the rockwell application

```bash
PYTHONPATH=src poetry run uvicorn rockwell.main:app --reload
```

The config files in both the front and backend must also be filled out and the database
tables in the DatabaseScript must be placed on a postgresql database.


# Deployment Steps
We deploy via docker, so make sure you have docker installed and that the docker daemon is running.
Make sure you also have docker compose plugin installed
Rockwell currently runs on port `8000`

```sh
sudo docker compose up --build
```

or 
```sh
docker compose up --build
```
