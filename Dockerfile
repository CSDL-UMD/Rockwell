FROM ubuntu:18.04
RUN mkdir /home/Client
copy . /home/Client
RUN apt-get -y update && \ 
    apt-get install nodejs -y&& \ 
    apt-get install npm -y 
    # This handles the Node dependencies

RUN apt-get install software-properties-common -y && \  
    apt-get install python3 -y && \ 
    apt-get upgrade python3 -y
    # or echo y | command if this doesnt work.