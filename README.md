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


# Deployment
Deployment to a server requires the use of tmux, nginx and gunicorn.

Each Flask API requires it's own gunicorn service file. Each file must be placed in /etc/systemd/system/, and the service file will have extension .service. Must install the python dependencies, as well as gunicorn, Flask, python-dotenv, flask-cors and requests in a virtual environment (requires python3-venv):
```
python3 -m venv .venv
source .venv/bin/activate
```

A single nginx (.nginx) file is required, and will be located in /etc/nginx/sites-available/. The following are the steps:
```
sudo rm /etc/nginx/sites-enabled/default
sudo vi /etc/nginx/sites-available/[nginx file name].nginx
sudo ln -s /etc/nginx/sites-available/[nginx file name].nginx /etc/nginx/sites-enabled/[nginx file name].nginx
```

To start the nginx server, run:
```
sudo systemctl reload nginx
```

To start the gunicorn service, run (for each app):
```
sudo systemctl daemon-reload
sudo systemctl start [app name, without the .service extension]
```

Sample files are provided in the scriptsAndFiles folder.
