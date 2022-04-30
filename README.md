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


# Deployment Steps
1. SSH into the your server where the app is located (or where you intend to clone it) (we assume Ubuntu):

2. Ensure that you have pip, nginx and npm installed:
  ```
  sudo apt-get update
  sudo apt install python3-pip
  sudo apt-get install nginx
  sudo apt install npm
  ```
  
3. Clone your repository into your server if you have not already done so already, using: 
  ```
  git clone [insert .git URL here]
  ```
  
4. Ensure that your directory has read and write permissions:
  ```
  sudo chmod 777 [insert root directory of app here]
  cd [insert root directory of app here]
  ```
  
The following steps are used to host the front-end:
1. cd into the front-end portion of your project

2. Install npm files, and build:
  ```
  sudo npm install
  sudo npm run build
  ```
  
3. We will now configure nginx:
  ```
  cd ~
  sudo rm /etc/nginx/sites-enabled/default
  sudo vi /etc/nginx/sites-available/[insert project name here].nginx
  ```
4. Please refer to this [sample nginx file](/scripts/Deployment/sample.nginx) for the contents of the nginx file

5.Link the sites-available and sites-enabled config files
  ```
  sudo ln -s /etc/nginx/sites-available/[insert project name here].nginx /etc/nginx/sites-enabled/[insert project name here].nginx
  ```
  
6. Now start the nginx server:
  ```
  sudo systemctl reload nginx
  ```

7. Important note, you must rebuild the app and reload nginx whenever the frontend is modified
  
The following steps are used to host the back-end:
1. cd into the backend portion of your project\

2. Create the pythonn virtual environment and install the python packages:
  ```
  sudo apt install python3-venv
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
  deactivate
  cd ~
  ```
  
3. We will now configure the gunicorn servers for all apps, starting with twauth-web
  ```
  sudo vi /etc/systemd/system/twauth-web.service
  ```

4. Please refer to the [sample file](scripts/Deployment/sample.service) for this service file's contents

5. Repeat steps 3 and 4, but now for twitterFeedGeneration.service, Retweet.service, and database_access.service

6. Now start the gunicorn servers for these apps:
  ```
  sudo systemctl daemon-reload
  sudo systemctl start twauth-web
  sudo systemctl start twitterFeedGeneration
  sudo systemctl start Retweet
  sudo systemctl start database_access
  ```
 
7. In order to check the statuses of these apps:
  ```
  sudo systemctl status twauth-web
  sudo systemctl status twitterFeedGeneration
  sudo systemctl status Retweet
  sudo systemctl status database_access
  ```
8. Important note: You must restart the services whenever the backend app is modified

The following information describes the use of tmux in order to run the eligibility app:
