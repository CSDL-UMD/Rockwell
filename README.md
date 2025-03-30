# Rockwell

Rockwell uses the twitter authentication workflow to render a twitter like feed in order to collect information about the users interaction with their feed. It also has an attention check feature to ensure that the user is being observant of their feeds and not simply scrolling through with the intent of finishing quickly.

# Tech Stack

Rockwell uses a PostgreSQL database, a Python (FastAPI) backend managed with Poetry, and a Node/React.js frontend.

# Installation

Make sure you have poetry installed

```bash
pip3 install poetry
poetry --version
```

Navigate to the project root folder and run:
```bash
pip install --no-root --no-interaction --no-ansi
```

Then run

```bash
PYTHONPATH=src poetry run uvicorn rockwell.main:app --reload
```

The config files in both the front and backend must also be filled out and the database
tables in the DatabaseScript must be placed on a postgresql database.


# Deployment Steps
We deploy via docker, so make sure you have docker installed and that the docker daemon is running.

1. Build the image
```bash
docker build -t rockwell-app .
```

2. Run the container
```bash
docker run -p 8000:8000 rockwell-app
```
