#!/bin/bash

if (($1 == 0))
then
    #tmux new-session -s NodeApp -d 'node ./app.js'
    tmux new-session -s Authorizer -d 'cd ./twitter_api/twauth-web-master/ && python3 ./twauth-web.py'
    tmux new-session -s FeedRendering -d 'cd ./twitter_api/guest_access_tweepy/ && python3 ./guest_access_twitter_flask.py'
    tmux new-session -s DatabaseAccess -d 'cd ./twitter_api/database_access/ && python3 ./database_access.py'
    tmux new-session -s Engagement -d 'cd ./twitter_api/engagement_servers/ && python3 ./Retweet.py'
elif (($1 == 1))
then
    #tmux kill-session -t NodeApp
    tmux kill-session -t Authorizer
    tmux kill-session -t FeedRendering
    tmux kill-session -t DatabaseAccess
    tmux kill-session -t Engagement
elif (($1 == 2))
then
    #tmux kill-session -t NodeApp
    tmux kill-session -t Authorizer
    tmux kill-session -t FeedRendering
    tmux kill-session -t DatabaseAccess
    tmux kill-session -t Engagement
    sleep 5
    #tmux new-session -s NodeApp -d 'node ./app.js'
    tmux new-session -s Authorizer -d 'cd ./twitter_api/twauth-web-master/ && python3 ./twauth-web.py'
    tmux new-session -s FeedRendering -d 'cd ./twitter_api/guest_access_tweepy/ && python3 ./guest_access_twitter_flask.py'
    tmux new-session -s DatabaseAccess -d 'cd ./twitter_api/database_access/ && python3 ./database_access.py'
    tmux new-session -s Engagement -d 'cd ./twitter_api/engagement_servers/ && python3 ./Retweet.py'
else
    echo "Enter 0 for start, 1 for stop, and 2 for restart as a command line argument."
fi
