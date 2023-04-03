#!/bin/bash

# Bash "strict" mode, see http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail
IFS=$'\n\t'

function usage () {
    echo "Usage: $0 [start|stop|restart]"
}

function startbackend () {
    echo -e "Starting backend..."
    #tmux new-session -s NodeApp -d 'node ./app.js'
    tmux new-session -s Authorizer -d 'cd ./src/authorizer/ && python3 ./twauth-web.py' || echo "Could not start Authorizer!"
    #tmux new-session -s Authorizer_Qualtrics -d 'cd ./src/authorizer/ && python3 ./auth_qualtrics.py' || echo "Could not start Qualtrics Authorizer!"
    tmux new-session -s FeedRendering -d 'cd ./src/feedGeneration/ && python3 ./twitterFeedGeneration.py' || echo "Could not start FeedRendering!"
    tmux new-session -s DatabaseAccess -d 'cd ./src/databaseAccess/ && python3 ./database_access.py' || echo "Could not start DatabaseAccess!"
    tmux new-session -s Engagement -d 'cd ./src/engagements/ && python3 ./Retweet.py' || echo "Could not start Engagement!"
    echo "done."
}

function stopbackend () {
    echo -e "Stopping backend..."
    #tmux kill-session -t NodeApp || echo "Could not kill NodeApp; check it is running."
    tmux kill-session -t Authorizer || echo "Could not kill Authorizer; check it is running."
    #tmux kill-session -t Authorizer_Qualtrics || echo "Could not kill Authorizer_Qualtrics; check it is running."
    tmux kill-session -t FeedRendering || echo "Could not kill FeedRendering; check it is running."
    tmux kill-session -t DatabaseAccess || echo "Could not kill DatabaseAccess; check it is running."
    tmux kill-session -t Engagement || echo "Could not kill Engagement; check it is running."
    echo "done."
}

if [[ $# -ne 1 ]] 
then
    echo "Error: not enough arguments!"
    usage
    exit -1
fi

if [[ $1 = "start" ]]
then
    startbackend
elif [[ $1 = "stop" ]]
then
    stopbackend
elif [[ $1 = "restart" ]]
then
    stopbackend
    sleep 5
    startbackend
else
    echo "Error: unknown command: $1" 
    usage
    exit -1
fi
