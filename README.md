# Rockwell

Rockwell uses the twitter authentication workflow to render a twitter like feed in order to collect information about the users interaction with their feed. It also has an attention check feature to ensure that the user is being observant of their feeds and not simply scrolling through with the intent of finishing quickly.

# Tech Stack

Rockwell uses a postgresql database, a python backend, and a Node/React.Js frontend.

# Installation
Navigate to the backend folder and run:
```
pip install -e .
```

Navigate to the frontend folder and run:
```
npm i
```

Use the bash script in the backend to run the backend servers (requires tmux) and run npm start
to spin up the front end.

The config files in both the front and backend must also be filled out and the database
tables in the DatabaseScript must be placed on a postgresql database.