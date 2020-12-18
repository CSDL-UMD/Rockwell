FROM ubuntu:18.04
RUN mkdir /home/Client
copy . /home/Client
RUN apt-get -y update && \ 
    apt-get install nodejs -y&& \ 
    apt-get install npm -y 
    # This handles the Node dependencies

RUN apt-get install software-properties-common -y && \  
    apt-get install python3 -y && \ 
    apt-get upgrade python3 -y && \ 
    apt-get install python3-pip -y
    # or echo y | command if this doesnt work.

RUN echo yes | pip3 install tweepy && \ 
    echo yes | pip3 install flask && \ 
    echo yes | pip3 install pandas && \
    echo yes | pip3 install requests
# Need to know what npm packages have to be installed to finish the proper installation. Python is confirmed working.