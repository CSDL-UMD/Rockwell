FROM ubuntu:18.04
RUN mkdir /home/Client
copy . /home/Client
RUN apt-get -y update && \ 
    apt-get install -y curl && \ 
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y nodejs
    #apt-get install nodejs -y&& \ 
    #apt-get install npm -y 
    # This handles the Node dependencies
# Install mongo stuff while we still need it
RUN apt-get install -y mongodb

RUN apt-get install software-properties-common -y && \  
    apt-get install python3 -y && \ 
    apt-get upgrade python3 -y && \ 
    apt-get install python3-pip -y
    # or echo y | command if this doesnt work.

#Installation of all python packages
RUN echo yes | pip3 install tweepy && \ 
    echo yes | pip3 install flask && \ 
    echo yes | pip3 install pandas && \
    echo yes | pip3 install requests
# Installation of all Node packages
RUN npm install npm -g && \ 
    npm install axios && \
    npm install lodash && \
    npm install bluebird && \ 
    npm install crypto && \ 
    npm install nodemailer && \ 
    npm install passport && \ 
    npm install moment && \ 
    npm install mongoose && \ 
    npm install bcrypt && \ 
    npm install express && \ 
    npm install compression && \ 
    npm install express-session && \ 
    npm install body-parser && \ 
    npm install morgan && \ 
    npm install chalk && \ 
    npm install errorhandler && \ 
    npm install lusca && \ 
    npm install dotenv && \ 
    npm install connect-mongo && \ 
    npm install express-flash && \ 
    npm install path && \ 
    npm install express-validator@5.3.1 && \ 
    npm install express-status-monitor && \ 
    npm install node-schedule && \ 
    npm install multer && \ 
    npm install request && \ 
    npm install passport-local && \  
    npm install async && \ 
    npm install fs && \ 
    npm install csvtojson && \ 
    npm install pug
#service mongodb start needs to be ran (Shell script to start it all up probably) We need to get rid of mongo stuff entirely from the app.js
EXPOSE 3000